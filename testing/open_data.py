import os

import imas
from imas import imasdef

from duqtools.api import ImasHandle

os.environ['IMAS_VERSION'] = '3.38.0'

user = ''
db = '/home/stef/python/duqtools/testing/imasdb/jet'
shot = 123
run = 1
ids = 'core_profiles'

entry = imas.DBEntry(imasdef.ASCII_BACKEND, db, shot, run, user)

ret = entry.open()
print(ret)

cp = entry.get(ids)
print(cp.time)

ret = entry.close()
print(ret)

h = ImasHandle(user=user, db=db, shot=shot, run=run)
h._backend = imasdef.ASCII_BACKEND

m = h.get(ids)
print(m)
print(m['time'])
