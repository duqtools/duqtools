from pathlib import Path

import imas

from duqtools.api import IDSMapping

data = Path('random_ds.ids').read_bytes()

ds = imas.distribution_sources()
ds.deserialize(data)

print(ds)

m = IDSMapping(ds)
print(m._keys)
