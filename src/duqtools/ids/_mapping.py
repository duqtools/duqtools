from __future__ import annotations

import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Sequence

import numpy as np
from imas2xarray import Variable, var_lookup

if TYPE_CHECKING:
    import xarray as xr

INDEX_STR = '*'


class EmptyVarError(Exception):
    ...


def insert_re_caret_dollar(string: str) -> str:
    """Insert regex start (^) / end ($) of line matching characters."""
    if not string.startswith('^'):
        string = f'^{string}'
    if not string.endswith('$'):
        string = f'{string}$'
    return string


def replace_index_str(string: str) -> str:
    """Replaces template string with regex digit matching."""
    return string.replace(INDEX_STR, r'(\d+)')


class IDSMapping(Mapping):

    def __init__(self, ids: Any) -> None:
        """Map the IMASDB object.

        Empty arrays are excluded from the mapping.
        You can still get/set these keys directly,
        but `key in map` returns `False` if `map['key']` is an empty array.

        Parameters
        ----------
        ids :
            IMAS DB entry for the IDS.

        Attributes
        ----------
        exclude_empty : bool
        """
        self._ids = ids

        # All available data fields are stored in this set.
        self._keys: set[str] = set()
        self._paths: dict[str, Any] = {}

        self.dive(ids, [])

    def __repr__(self):
        s = f'{self.__class__.__name__}(\n'
        for key in self._paths:
            s += f'  {key} = ...\n'
        s += ')\n'

        return s

    @staticmethod
    def _getattr(pointer: Any, attr: str) -> Any:
        """Like `getattr`, but will return the index if `attr` is an int."""
        try:
            i = int(attr)
        except (ValueError, TypeError):
            ret = getattr(pointer, attr)
        else:
            ret = pointer[i]  # type: ignore

        return ret

    def _deconstruct_key(self, key: str) -> tuple[Any, str]:
        """Break down key and return pointer + attr."""
        *parts, attr = key.split('/')

        pointer = self._ids

        for part in parts:
            pointer = self._getattr(pointer, part)

        return pointer, attr

    def __getitem__(self, key: str) -> Any:

        try:
            pointer, attr = self._deconstruct_key(key)
            ret = self._getattr(pointer, attr)
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

    @staticmethod
    def _path_at_index(variable: str | Variable, index: int | Sequence[int]):
        path = variable.path if isinstance(variable, Variable) else variable

        if isinstance(index, int):
            index = (index, )

        for i in index:
            path = path.replace('*', str(i), 1)

        return path

    def get_at_index(self, variable: str | Variable,
                     index: int | Sequence[int], **kwargs) -> Any:
        """Grab key with index replacement.

        Example: `IDSMapping.get_at_index(var, index=0)`
        """
        path = self._path_at_index(variable, index)
        return self[path]

    def set_at_index(self, variable: str | Variable,
                     index: int | Sequence[int], value: Any, **kwargs):
        """Grab key with index replacement.

        Example: `IDSMapping.set_at_index(var, value, index=0)`
        """
        path = self._path_at_index(variable, index)
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

    def dive(self, val, path: list):
        """Recursively find the data fields.

        Parameters
        ----------
        val :
            Current nested object being evaluated
        path : list
            Current path
        """

        if isinstance(val, str):
            return

        if hasattr(val,
                   '__getitem__') and not isinstance(val,
                                                     (np.ndarray, np.generic, dict)):
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

        if val.size == 0:
            return

        # We made it here, the value can be stored
        str_path = '/'.join(path)
        self._keys.add(str_path)

        cur = self._paths
        for part in path[:-1]:
            cur.setdefault(part, {})
            cur = cur[part]
        cur[path[-1]] = str_path

    def findall(self, pattern: str) -> dict[str, Any]:
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
        pattern = replace_index_str(pattern)

        pat = re.compile(pattern)

        return {key: self[key] for key in self._keys if pat.match(key)}

    def find_by_group(self, pattern: str) -> dict[tuple | str, Any]:
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
        pattern = replace_index_str(pattern)

        pat = re.compile(pattern)

        new = {}
        for key in self._keys:
            m = pat.match(key)
            if m:
                groups = m.groups()
                idx = groups[0] if len(groups) == 1 else groups
                new[idx] = self[key]

        return new

    def _read_array_from_parts(self, *parts: str):
        arr = []
        root, sub, *remaining = parts
        nodes = self[root]

        for index in range(len(nodes)):
            path = f'{root}/{index}/{sub}'

            if remaining:
                sub_arr = self._read_array_from_parts(path, *remaining)
            else:
                sub_arr = self[path]

            arr.append(sub_arr)

        return arr

    def to_xarray(
        self,
        variables: Sequence[str | Variable],
        empty_var_ok: bool = False,
        **kwargs,
    ) -> xr.Dataset:
        """Return dataset for given variables.

        Parameters
        ----------
        variables : Sequence[str | Variable]]
            Dictionary of data variables
        empty_var_ok : bool
            If True, silently skip data that are missing from the mapping.
            If False (default), raise an error when data that are missing
            from the dataset are requested.

        Returns
        -------
        ds : xr.Dataset
            Return query as Dataset
        """

        def _contains_empty(arr):
            if isinstance(arr, list):
                if len(arr) == 0:
                    return True
                return any(_contains_empty(sub_arr) for sub_arr in arr)
            elif isinstance(arr, np.ndarray):
                return arr.size == 0
            elif isinstance(arr, (float, int)):
                return False
            else:
                raise ValueError(
                    f"Don't know how to deal with: {var.name}: {arr}")

        import xarray as xr

        xr_data_vars: dict[str, tuple[list[str], np.ndarray]] = {}

        var_models = var_lookup.lookup(variables)

        for var in var_models:
            parts = var.path.split('/*/')

            if len(parts) == 1:
                xr_data_vars[var.name] = (var.dims, self[var.path])
                continue

            arr = self._read_array_from_parts(*parts)

            if _contains_empty(arr):
                if empty_var_ok:
                    continue
                else:
                    raise EmptyVarError(
                        f'Variable {var.name!r} contains empty data.')
            xr_data_vars[var.name] = ([*var.dims], arr)

        ds = xr.Dataset(data_vars=xr_data_vars)  # type: ignore

        return ds

    def _write_array_in_parts(self, data, *parts: str) -> None:
        """_write_array_in_parts.

        inner function that determines the path and writes back the data
        """
        if len(parts) < 2:
            # Write back
            path, = parts
            self[path] = data
            return

        root, sub, *remaining = parts
        nodes = self[root]
        for index in range(len(nodes)):
            path = f'{root}/{index}/{sub}'
            self._write_array_in_parts(data[index], path, *remaining)

    def write_array_in_parts(self, variable_path: str,
                             data: xr.DataArray) -> None:
        """write_back data, give the data, and the variable path, where `*`
        denotes the dimensions. This function will figure out how to write it
        back to the IDS.

        Parameters
        ----------
        variable_path : str
            path of the variable in the IDS, something like 'profiles_1d/*/zeff'
        data : xr.DataArray
            data of the variable, in the correct dimensions (every star in the
            `variable_path` is a dimension in this array)

        Returns
        -------
        None
        """
        parts = variable_path.split('/*/')
        self._write_array_in_parts(data.data, *parts)
