from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ._mapping import IDSMapping

if TYPE_CHECKING:
    from .ids import ImasHandle

logger = logging.getLogger(__name__)


def get_ids_tree(imas_loc: ImasHandle,
                 key: str = 'core_profiles',
                 **kwargs) -> IDSMapping:
    """get the data as a simple ids (all values in memory, in a dict).

    Parameters
    ----------
    key : str, optional
        Name of profiles to open
    **kwargs
        These parameters are passed to initialize `IDSMapping`.

    Returns
    -------
    IDSMapping
    """
    return IDSMapping(imas_loc.get(key), **kwargs)
