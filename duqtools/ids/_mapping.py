import re
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, Dict, Union

import numpy as np


def insert_re_caret_dollar(string: str) -> str:
    """Insert regex start (^) / end ($) of line matching characters."""
    if not string.startswith('^'):
        string = f'^{string}'
    if not string.endswith('$'):
        string = f'{string}$'
    return string


def recursive_defaultdict():
    """Recursive defaultdict."""
    return defaultdict(recursive_defaultdict)


def defaultdict_to_dict(ddict: defaultdict):
    """defaultdict_to_dict, turns a nested defaultdict into a nested dict.

    Parameters
    ----------
    ddict : defaultdict
        ddict
    """

    # Convert members to dict first
    for k, v in ddict.items():
        if isinstance(v, defaultdict):
            ddict[k] = defaultdict_to_dict(v)
    # Finally convert self to dict
    return dict(ddict)


class IDSMapping(Mapping):

    def __init__(self, ids, exclude_empty: bool = True):
        self._ids = ids
        self.exclude_empty = exclude_empty

        # All fields in the core profile in a single dict
        self.flat_fields: dict = {}

        # All fields, in the core profile in a nested dict
        self.fields: dict = defaultdict(recursive_defaultdict)

        self.dive(ids, [])
        self.fields = defaultdict_to_dict(self.fields)

    def __repr__(self):
        s = f'{self.__class__.__name__}(\n'
        for key in self.fields.keys():
            s += f'  {key} = ...\n'
        s += ')\n'

        return s

    def __getitem__(self, key: str):
        try:
            return self.flat_fields[key]
        except KeyError:
            pass
        try:
            return self.fields[key]
        except KeyError:
            raise

    def __iter__(self):
        yield from self.fields

    def __len__(self):
        return len(self.fields)

    def dive(self, val, path: list):
        """Recursively store the important bits of the imas structure in dicts.

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
        self.flat_fields['/'.join(path)] = val
        cur = self.fields
        for item in path[:-1]:
            cur = cur[item]
        cur[path[-1]] = val

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

        pat = re.compile(pattern)

        return {
            key: self.flat_fields[key]
            for key in self.flat_fields if pat.match(key)
        }

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

        pat = re.compile(pattern)

        new = {}
        for key in self.flat_fields:
            m = pat.match(key)
            if m:
                groups = m.groups()
                idx = groups[0] if len(groups) == 1 else groups
                new[idx] = self.flat_fields[key]

        return new

    def find_by_index(self, pattern: str) -> Dict[str, Dict[int, np.ndarray]]:
        """Find keys matching regex pattern using time index.

        Must include $i, which is a special character that matches
        an integer (`\\d+`)

        i.e. `ids.find_by_index('profiles_1d/$i/zeff.*')`
        returns a dict with `zeff` and error attributes.

        Parameters`
        ----------
        pattern : str
            Regex pattern, must include a group matching a digit.

        Returns
        -------
        dict
            New dict with all matching key/value pairs.
        """
        idx_str = '$i'

        if idx_str not in pattern:
            raise ValueError(f'Pattern must include {idx_str} to match index.')

        pattern = insert_re_caret_dollar(pattern)

        pattern = pattern.replace(idx_str, r'(?P<idx>\d+)')
        pat = re.compile(pattern)

        new_dict: Dict[str, Dict[int, np.ndarray]] = defaultdict(dict)

        for key in self.flat_fields:
            m = pat.match(key)

            if m:
                si, sj = m.span('idx')
                new_key = key[:si] + idx_str + key[sj:]

                idx = int(m.group('idx'))
                new_dict[new_key][idx] = self.flat_fields[key]

        return new_dict
