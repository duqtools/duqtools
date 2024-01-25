from __future__ import annotations

import os
from typing import Type, Union

from ._hdf5handle import HDF5ImasHandle
from ._mdsplushandle import MDSPlusImasHandle

ImasHandleType = Type[Union[HDF5ImasHandle, MDSPlusImasHandle]]
ImasHandle: ImasHandleType

backend = os.environ.get('JINTRAC_IMAS_BACKEND')

if backend == 'MDSPLUS':
    ImasHandle = MDSPlusImasHandle
elif backend == 'HDF5':
    ImasHandle = HDF5ImasHandle
else:
    ImasHandle = MDSPlusImasHandle
