from __future__ import annotations

import logging

from .config import cfg
from .ids import ImasHandle, merge_data
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def merge(**kwargs):
    """Merge data."""
    template = ImasHandle.parse_obj(cfg.merge.template)
    target = ImasHandle.parse_obj(cfg.merge.output)

    handles = read_imas_handles_from_file(cfg.merge.data)

    for step in cfg.merge.plan:
        debug('Merge input: %s', template)
        debug('Merge output: %s', target)

        template.copy_data_to(target)

        merge_data(source_data=handles,
                   target=target,
                   x_var=step.grid_variable,
                   y_vars=step.variables)
