from imas.imasdef import ASCII_SERIALIZER_PROTOCOL

from duqtools.api import ImasHandle

h = ImasHandle.from_string('root/jet/123/1')
assert h.exists()

m = h.get('core_profiles')

with open('core_profiles.ids', 'w') as f:
    # If you use `deserialize`, you must add the left chevron
    # For loading via imas.DBEntry, do not add the chevron
    # f.write('<')
    f.write(m._ids.serialize(protocol=ASCII_SERIALIZER_PROTOCOL).decode())
