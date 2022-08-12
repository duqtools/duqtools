from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Sequence, Union

from ._handle import ImasHandle

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import pandas as pd


def _get_ids_run_dataframe(handle: ImasHandle,
                           *,
                           ids: str = 'core_profiles',
                           keys: Sequence[str],
                           **kwargs) -> pd.DataFrame:
    """Get data for single run."""
    logger.info('Getting data for %s', handle)
    data = handle.get(ids, exclude_empty=True)
    return data.to_dataframe(*keys, **kwargs)


def get_ids_dataframe(handles: Union[Sequence[ImasHandle],
                                     Dict[str, ImasHandle]], *, ids: str,
                      keys: Sequence[str], **kwargs) -> pd.DataFrame:
    """Read a dict of IMAS handles into a structured pandas dataframe.

    The returned dataframe will have the columns:

        `run`, `tsteps`, `times`, `<ids col 1>, `<ids_col_2>`, ...

    Where `tstep` corresponds to the time index, and `times` to the
    actual times.

    Parameters
    ----------
    handles : Union[Sequence[str], Dict[str, ImasHandle]]
        Dict with IMAS handles. The key is used as the 'run' name in
        the dataframe. If the handles are specified as a sequence,
        The Imas string representation will be used as the key.
    ids : str
        IDS to extract data from (e.g. `'core_profiles'`).
    keys : Sequence[str]
        IDS keys to extract. These will be used as columns in the
        data frame.
    **kwargs
        These keyword parameters are passed to
        `duqtools.ids.IDSMapping.to_dataframe`.

    Returns
    -------
    pd.DataFrame
        Structured pandas dataframe.
    """
    import pandas as pd

    if not isinstance(handles, dict):
        handles = {handle.to_string(): handle for handle in handles}

    runs_data = {
        str(name): _get_ids_run_dataframe(handle, ids=ids, keys=keys, **kwargs)
        for name, handle in handles.items()
    }

    return pd.concat(runs_data,
                     names=('run',
                            'index')).reset_index('run').reset_index(drop=True)
