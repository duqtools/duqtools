from collections import defaultdict


def recursive_defaultdict():
    return defaultdict(recursive_defaultdict)


class SimpleCoreIDS:

    flat_fields: dict = {}  # All fields in the core profile in a single dict
    fields: defaultdict = defaultdict(
        recursive_defaultdict
    )  # All fields, in the core profile in a nested dict

    def __init__(self, ids):
        self.dive(ids, [ids.__name__])

    def dive(self, val, path):
        skip = False
        if isinstance(val, str):
            skip = True

        if isinstance(val, list) and not skip:
            for i in range(len(val)):
                item = val[i]
                self.dive(item, path + [str(i)])
            return

        if not hasattr(val, '__dict__'):
            skip = True

        if not skip:
            for key, item in val.__dict__.items():
                self.dive(item, path + [key])
        else:
            self.flat_fields['/'.join(path)] = val
            cur = self.fields
            for item in path[:-1]:
                cur = cur[item]
            cur[path[-1]] = val
