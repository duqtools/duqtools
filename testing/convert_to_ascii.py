from imas.imasdef import ASCII_SERIALIZER_PROTOCOL

from duqtools.api import ImasHandle

h = ImasHandle.from_string('root/jet/123/1')
assert h.exists()

m = h.get('core_profiles')

with open('core_profiles.ids', 'w') as f:
    # IDS must start with chevron
    # bytes representation of first char
    # defines serializer protocol on read
    f.write('<')
    f.write(m._ids.serialize(protocol=ASCII_SERIALIZER_PROTOCOL).decode())
