from __future__ import annotations

import os

from ._hdf5handle import HDF5ImasHandle
from ._mdsplushandle import MdsplusImasHandle

backend = os.environ.get('JINTRAC_IMAS_BACKEND', 'HDF5')

if backend == 'MDSPLUS':
    ImasHandle = MdsplusImasHandle  # type: ignore
elif backend == 'HDF5':
    ImasHandle = HDF5ImasHandle  # type: ignore
else:
    ImasHandle = HDF5ImasHandle  # type: ignore
