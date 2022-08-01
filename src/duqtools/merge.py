from __future__ import annotations

import logging

from .config import cfg
from .ids import ImasHandle, get_ids_dataframe, merge_data
from .models import WorkDirectory
from .operations import confirm_operations
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


@confirm_operations
def merge(**kwargs):
    """Merge data."""

    workspace = WorkDirectory.parse_obj(cfg.workspace)

    template = ImasHandle.parse_obj(cfg.merge.template)
    target = ImasHandle.parse_obj(cfg.merge.output)

    prefix = cfg.merge.prefix
    x_val = cfg.merge.base_ids
    y_vals = cfg.merge.ids_to_merge

    handles = read_imas_handles_from_file(workspace.runs_yaml)

    data = get_ids_dataframe(handles, keys=(x_val, *y_vals), prefix=prefix)

    debug('Merge input: %s', template)
    debug('Merge output: %s', target)

    template.copy_data_to(target)

    merge_data(data=data,
               target=target,
               x_val=x_val,
               y_vals=y_vals,
               prefix=cfg.merge.prefix)
