from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Dict, List, Sequence, Set, Tuple, Union

import numpy as np

from ..schema import VariableModel
from ._constants import TIME_COL, TSTEP_COL
from ._copy import add_provenance_info
from ._variable import Variable

if TYPE_CHECKING:
    import pandas as pd
    import xarray as xr

    from ._handle import ImasHandle

TIME_STR = '$time'


def insert_re_caret_dollar(string: str) -> str:
    """Insert regex start (^) / end ($) of line matching characters."""
    if not string.startswith('^'):
        string = f'^{string}'
    if not string.endswith('$'):
        string = f'{string}$'
    return string


def replace_time_str(string: str) -> str:
    """Replaces template string with regex digit matching."""
    return string.replace(TIME_STR, r'(?P<idx>\d+)')


class IDSMapping(Mapping):

    def __init__(self, ids, exclude_empty: bool = True):
        """__init__

        Parameters
        ----------
        ids :
            IMAS DB entry for the IDS.
        exclude_empty : bool
            Hide empty arrays from mapping. You can still get/set these keys directly,
            but `key in map` returns `False` if `map['key']` is an empty array.
        """
        self._ids = ids
        self.exclude_empty = exclude_empty

        # All available data fields are stored in this set.
        self._keys: Set[str] = set()
        self._paths: Dict[str, Any] = {}

        self.dive(ids, [])

    def __repr__(self):
        s = f'{self.__class__.__name__}(\n'
        for key in self._paths:
            s += f'  {key} = ...\n'
        s += ')\n'

        return s

    def _deconstruct_key(self, key: str):
        """Break down key and return pointer + attr."""
        *parts, attr = key.split('/')

        pointer = self._ids

        for part in parts:
            try:
                i = int(part)
            except ValueError:
                pointer = getattr(pointer, part)
            else:
                pointer = pointer[i]

        return pointer, attr

    def __getitem__(self, key: str):

        try:
            pointer, attr = self._deconstruct_key(key)
            ret = getattr(pointer, attr)
        except AttributeError as err:
            raise KeyError(key) from err
        except IndexError as err:
            raise KeyError(key) from err

        return ret

    def __setitem__(self, key: str, value: np.ndarray):

        try:
            pointer, attr = self._deconstruct_key(key)
            getattr(pointer, attr)
        except AttributeError as err:
            raise KeyError(key) from err
        except IndexError as err:
            raise KeyError(key) from err
        else:
            setattr(pointer, attr, value)

    def __iter__(self):
        yield from self._keys

    def __len__(self):
        return len(self._keys)

    def __contains__(self, key):
        return key in self._keys

    def get_with_replace(self, variable: Union[str, VariableModel],
                         **kwargs) -> Any:
        """Grab key with placeholder replacement.

        Example: `IDSMapping.get_with_replace(var, time=0)`
        """
        path = variable.path if isinstance(variable,
                                           VariableModel) else variable

        for old, new in kwargs.items():
            path = path.replace(f'${old}', str(new))

        return self[path]

    def set_with_replace(self, variable: Union[str, VariableModel], value: Any,
                         **kwargs):
        """Grab key with placeholder replacement.

        Example: `IDSMapping.set_with_replace(var, value, time=0)`
        """
        path = variable.path if isinstance(variable,
                                           VariableModel) else variable

        for old, new in kwargs.items():
            path = path.replace(f'${old}', str(new))

        self[path] = value

    def length_of_key(self, key: str):
        """length_of_key gives you the number of entries of a (partial) ids
        path, or None if the length does not exist.

        Note: this is different then the length of an IDSMapping, which is defined
        as the number of keys

        Note: calling `len(map[key])` works as well

        ## Example:


        ```python
        map.length_of_key('1d_profiles')
        ```

        Parameters
        ----------
        key : str
            key
        """
        try:
            return len(self[key])
        except Exception:
            pass

    def sync(self, target: ImasHandle):
        """Synchronize updated data back to IMAS db entry.

        Shortcut for 'put' command.

        Parameters
        ----------
        target : ImasHandle
            Points to an IMAS db entry of where the data should be written.
        """

        add_provenance_info(handle=target)

        with target.open() as db_entry:
            self._ids.put(db_entry=db_entry)

    def dive(self, val, path: list):
        """Recursively find the data fields.

        Parameters
        ----------
        val :
            Current nested object being evaluated
        path : List
            Current path
        """

        if isinstance(val, str):
            return

        if hasattr(val,
                   '__getitem__') and not isinstance(val,
                                                     (np.ndarray, np.generic)):
            for i in range(len(val)):
                item = val[i]
                self.dive(item, path + [str(i)])
            return

        if hasattr(val, '__dict__'):
            for key, item in val.__dict__.items():
                self.dive(item, path + [key])
            return

        if not isinstance(val, (np.ndarray, np.generic)):
            return

        if self.exclude_empty and val.size == 0:
            return

        # We made it here, the value can be stored
        str_path = '/'.join(path)
        self._keys.add(str_path)

        cur = self._paths
        for part in path[:-1]:
            cur.setdefault(part, {})
            cur = cur[part]
        cur[path[-1]] = str_path

    def findall(self, pattern: str) -> Dict[str, Any]:
        """Find keys matching regex pattern.

        Parameters
        ----------
        pattern : str
            Regex pattern

        Returns
        -------
        dict
            New dict with all matching key/value pairs.
        """
        pattern = insert_re_caret_dollar(pattern)
        pattern = replace_time_str(pattern)

        pat = re.compile(pattern)

        return {key: self[key] for key in self._keys if pat.match(key)}

    def find_by_group(self, pattern: str) -> Dict[Union[tuple, str], Any]:
        """Find keys matching regex pattern by group.

        The dict key is defined by `match.groups()`.
        Dict entries will be overwritten if the groups are not unique.

        Parameters
        ----------
        pattern : str
            Regex pattern (must contain groups)

        Returns
        -------
        dict
            New dict with all matching key/value pairs.
        """
        pattern = insert_re_caret_dollar(pattern)
        pattern = replace_time_str(pattern)

        pat = re.compile(pattern)

        new = {}
        for key in self._keys:
            m = pat.match(key)
            if m:
                groups = m.groups()
                idx = groups[0] if len(groups) == 1 else groups
                new[idx] = self[key]

        return new

    def find_by_index(self, pattern: str) -> Dict[str, Dict[int, np.ndarray]]:
        """Find keys matching regex pattern using time index.

        Must include $time, which is a special character that matches
        an integer time step (`\\d+`)

        i.e. `ids.find_by_index('profiles_1d/$time/zeff.*')`
        returns a dict with `zeff` and error attributes.

        Parameters
        ----------
        pattern : str
            Regex pattern, must include a group matching a digit.

        Returns
        -------
        dict
            New dict with all matching key/value pairs.
        """
        if TIME_STR not in pattern:
            raise ValueError(
                f'Pattern must include ../{TIME_STR}/.. to match index.')

        pattern = insert_re_caret_dollar(pattern)
        pattern = replace_time_str(pattern)

        pat = re.compile(pattern)

        new_dict: Dict[str, Dict[int, np.ndarray]] = defaultdict(dict)

        for key in self._keys:
            m = pat.match(key)

            if m:
                si, sj = m.span('idx')
                new_key = key[:si] + TIME_STR + key[sj:]

                idx = int(m.group('idx'))
                new_dict[new_key][idx] = self[key]

        return new_dict

    def to_dataframe(self,
                     *variables: str,
                     prefix: str = 'profiles_1d',
                     time_steps: Sequence[int] = None) -> pd.DataFrame:
        """Return long format dataframe for given variables.

        Search string:
        `{prefix}/{time_step}/{variable}`

        Parameters
        ----------
        *variables : str
            Keys to extract, i.e. `zeff`, `grid/rho_tor`
        prefix : str, optional
            First part of the data path
        time_steps : Sequence[int], optional
            List or array of integer time steps to extract.
            Defaults to all time steps.

        Returns
        -------
        df : pd.DataFrame
            Contains a column for the time step and each of the variables.
        """
        import pandas as pd
        columns, arr = self.to_numpy(*variables,
                                     prefix=prefix,
                                     time_steps=time_steps)

        df = pd.DataFrame(arr, columns=columns)
        df[TSTEP_COL] = df[TSTEP_COL].astype(int)

        return df

    def _fill_array_from_parts(self, *parts: str):
        arr = []
        root, sub, *remaining = parts
        nodes = self[root]
        
        for index in range(len(nodes)):
            path = f'{root}/{index}/{sub}'
            
            if remaining:
                sub_arr = self._fill_array_from_parts(path, *remaining)
            else:
                sub_arr = self[path]
            
            arr.append(sub_arr)

        return arr
    def to_xarray(
        self,
        variables: Sequence[Variable],
        **kwargs,
    ) -> xr.Dataset:
        """Return dataset for given variables.

        Parameters
        ----------
        variables : Dict[str, Variable]
            Dictionary of data variables

        Returns
        -------
        ds : xr.Dataset
            Return query as Dataset
        """
        import xarray as xr

        xr_data_vars: Dict[str, Tuple[List[str], np.array]] = {}

        for var in variables:
            parts = var.path.split('/*/')

            if len(parts) == 1:
                xr_data_vars[var.name] = (var.dims, self[var.path])
                continue

            arr = self._fill_array_from_partial_path(partial_path)

            xr_data_vars[var.name] = ([*var.dims], arr)

        ds = xr.Dataset(data_vars=xr_data_vars)

        return ds

    def to_numpy(
        self,
        *variables: str,
        prefix: str = 'profiles_1d',
        time_steps: Sequence[int] = None
    ) -> Tuple[Tuple[str, ...], np.ndarray]:
        """Return numpy array containing data for given variables.

        Search string:
        `{prefix}/{time_step}/{variable}`

        Parameters
        ----------
        *variables : str
            Keys to extract, i.e. `zeff`, `grid/rho_tor`
        prefix : str, optional
            First part of the data path
        time_steps : Sequence[int], optional
            List or array of integer time steps to extract.
            Defaults to all time steps.

        Returns
        -------
        columns, array : Tuple[Tuple[str], np.ndarray]
            Numpy array with a column for the time step and each of the
            variables.
        """
        points_per_var = len(self[f'{prefix}/0/{variables[0]}'])

        if not time_steps:
            n_time_steps = len(self[TIME_COL])
            time_steps = range(n_time_steps)
        else:
            n_time_steps = len(time_steps)

        columns = (TSTEP_COL, TIME_COL, *variables)
        n_vars = len(columns)

        arr = np.empty((n_time_steps * points_per_var, n_vars))

        timestamps = self[TIME_COL]

        for t in time_steps:
            for j, variable in enumerate(variables):
                flat_variable = f'{prefix}/{t}/{variable}'

                i_begin = t * points_per_var
                i_end = i_begin + points_per_var

                arr[i_begin:i_end, 0] = t
                arr[i_begin:i_end, 1] = timestamps[t]
                arr[i_begin:i_end, j + 2] = self[flat_variable]

        return columns, arr
