import os

import imas
from imas import imasdef

os.environ['IMAS_VERSION'] = '3.38.0'

entry = imas.DBEntry(imasdef.ASCII_BACKEND,
                     '/home/stef/python/duqtools/testing/imasdb/jet', 123, 1)

ret = entry.open()
print(ret)

cp = entry.get('core_profiles')

ret = entry.close()
print(ret)
