from __future__ import annotations

import logging
import os
from typing import Type, Union

from ._imas import imas_mocked
from ._mapping import IDSMapping
from ._merge import merge_data
from ._rebase import (
    rebase_all_coords,
    rebase_on_grid,
    rebase_on_time,
    rezero_time,
    squash_placeholders,
    standardize_grid,
    standardize_grid_and_time,
)

logger = logging.getLogger(__name__)

ImasHandleType = Type[Union[HDF5ImasHandle, MDSPlusImasHandle]]
ImasHandle: ImasHandleType

if os.environ['JINTRAC_IMAS_BACKEND'] == 'MDSPLUS':
    from ._mdsplushandle import MDSPlusImasHandle
    ImasHandle = MDSPlusImasHandle
elif os.environ['JINTRAC_IMAS_BACKEND'] == 'HDF5':
    from ._hdf5handle import HDF5ImasHandle
    ImasHandle = HDF5ImasHandle
else:
    from ._mdsplushandle import MDSPlusImasHandle
    ImasHandle = MDSPlusImasHandle

__all__ = [
    'IDSMapping',
    'ImasHandle',
    'ImasHandleType',
    'merge_data',
    'rebase_on_grid',
    'rebase_on_time',
    'rebase_all_coords',
    'standardize_grid_and_time',
    'standardize_grid',
    'rezero_time',
    'squash_placeholders',
    'imas_mocked',
]
