from __future__ import annotations

import os
from ._mdsplushandle import MdsplusImasHandle
from ._hdf5handle import HDF5ImasHandle

if os.environ['JINTRAC_IMAS_BACKEND']=='MDSPLUS':
    ImasHandle = MdsplusImasHandle
elif os.environ['JINTRAC_IMAS_BACKEND']=='HDF5':
    ImasHandle = HDF5ImasHandle
else:
    ImasHandle = MdsplusImasHandle
