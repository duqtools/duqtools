from pathlib import Path

import imas

from duqtools.api import IDSMapping

data = Path('core_profiles.ids').read_bytes()

cp = imas.core_profiles()
cp.deserialize(data)

print(cp)

m = IDSMapping(cp)
print(m._keys)
