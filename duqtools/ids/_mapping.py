import re
from collections import defaultdict
from collections.abc import Mapping

import numpy as np


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

    def __init__(self, ids):
        self._ids = ids

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

        # We made it here, the value can be stored
        self.flat_fields['/'.join(path)] = val
        cur = self.fields
        for item in path[:-1]:
            cur = cur[item]
        cur[path[-1]] = val

    def findall(self, pattern: str):
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
        pat = re.compile(pattern)
        return {
            key: self.flat_fields[key]
            for key in self.flat_fields if pat.match(key)
        }
