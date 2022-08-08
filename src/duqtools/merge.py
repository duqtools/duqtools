from __future__ import annotations

import logging
from typing import Sequence, Tuple

from .config import cfg
from .ids import ImasHandle, get_ids_dataframe, merge_data
from .operations import confirm_operations
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def _split_paths(paths: Sequence[str]) -> Tuple[str, Tuple[str, ...]]:
    """Split paths into its common prefix and keys.

    Parameters
    ----------
    paths : Sequence[str]
        Paths that can be found in the IDS entry. Must contain
        `/*/` to denote the time component.

    Returns
    -------
    prefix, keys : Tuple[str, List[str]]
        Return the common prefix and corresponding keys.
    """

    split_paths = (path.split('/*/') for path in paths)

    prefixes, keys = zip(*split_paths)

    prefix_set = set(prefixes)
    if not len(prefix_set) == 1:
        raise ValueError(
            f'All keys must have the same prefix, got {prefix_set}')

    return prefixes[0], keys


@confirm_operations
def merge(**kwargs):
    """Merge data."""
    template = ImasHandle.parse_obj(cfg.merge.template)
    target = ImasHandle.parse_obj(cfg.merge.output)

    handles = read_imas_handles_from_file(cfg.merge.data)

    for step in cfg.merge.plan:
        prefix, (x_val, *y_vals) = _split_paths(paths=(step.base_grid,
                                                       *step.paths))

        data = get_ids_dataframe(handles,
                                 ids=step.ids,
                                 keys=(x_val, *y_vals),
                                 prefix=prefix)

        debug('Merge input: %s', template)
        debug('Merge output: %s', target)

        template.copy_data_to(target)

        merge_data(data=data,
                   target=target,
                   x_val=x_val,
                   y_vals=y_vals,
                   prefix=prefix,
                   ids=step.ids)
