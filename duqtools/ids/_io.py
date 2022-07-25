from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict

from ._get_ids_tree import get_ids_tree
from ._handle import ImasHandle

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import pandas as pd


def _get_ids_run_dataframe(handle: ImasHandle, *, keys,
                           **kwargs) -> pd.DataFrame:
    """Get data for single run."""
    logger.info('Getting data for %s', handle)
    profile = get_ids_tree(handle, exclude_empty=True)
    return profile.to_dataframe(*keys, **kwargs)


def get_ids_dataframe(handles: Dict[str, ImasHandle],
                      **kwargs) -> pd.DataFrame:
    """Get and concatanate data for all runs."""
    import pandas as pd

    runs_data = {
        str(name): _get_ids_run_dataframe(handle, **kwargs)
        for name, handle in handles.items()
    }

    return pd.concat(runs_data,
                     names=('run',
                            'index')).reset_index('run').reset_index(drop=True)
