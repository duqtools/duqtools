from __future__ import annotations

import logging

from .config import cfg
from .ids import ImasHandle, get_ids_dataframe, merge_data
from .operations import confirm_operations
from .utils import read_imas_handles_from_file, split_paths

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


@confirm_operations
def merge(**kwargs):
    """Merge data."""
    template = ImasHandle.parse_obj(cfg.merge.template)
    target = ImasHandle.parse_obj(cfg.merge.output)

    handles = read_imas_handles_from_file(cfg.merge.data)

    for step in cfg.merge.plan:
        prefix, (x_val, *y_vals) = split_paths(paths=(step.base_grid,
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
