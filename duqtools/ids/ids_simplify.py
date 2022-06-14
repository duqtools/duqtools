from collections import defaultdict

import numpy as np


def recursive_defaultdict():
    return defaultdict(recursive_defaultdict)


class SimpleCoreIDS:
    # All fields in the core profile in a single dict
    flat_fields: dict = {}
    # All fields, in the core profile in a nested dict
    fields: defaultdict = defaultdict(recursive_defaultdict)

    def __init__(self, ids):
        self.dive(ids, [])

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
