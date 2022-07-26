from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Sequence

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


def get_ids_dataframe(handles: Dict[str, ImasHandle], *, keys: Sequence[str],
                      **kwargs) -> pd.DataFrame:
    """Read a dict of IMAS handles into a structured pandas dataframe.

    The returned dataframe will have the columns:

        `run`, `tsteps`, `times`, `<ids col 1>, `<ids_col_2>`, ...

    Where `tstep` corresponds to the time index, and `times` to the
    actual times.

    Parameters
    ----------
    handles : Dict[str, ImasHandle]
        Dict with IMAS handles. The key is used as the 'run' name in
        the dataframe.
    keys : Sequence[str]
        IDS values to extract. These will be used as columns in the
        data frame.
    **kwargs
        These keyword parameters are passed to
        `duqtools.ids.IDSMapping.to_dataframe`.

    Returns
    -------
    pd.DataFrame
        Description
    """
    import pandas as pd

    runs_data = {
        str(name): _get_ids_run_dataframe(handle, keys=keys, **kwargs)
        for name, handle in handles.items()
    }

    return pd.concat(runs_data,
                     names=('run',
                            'index')).reset_index('run').reset_index(drop=True)
