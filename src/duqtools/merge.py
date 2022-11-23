from __future__ import annotations

import logging

from .config import cfg, var_lookup
from .ids import ImasHandle, merge_data
from .utils import partition, read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def merge(**kwargs):
    """Merge as many data as possible."""
    template = ImasHandle.parse_obj(cfg.merge.template)
    target = ImasHandle.parse_obj(cfg.merge.output)

    handles = read_imas_handles_from_file(cfg.merge.data).values()

    debug('Merge input: %s', template)
    debug('Merge output: %s', target)

    template.copy_data_to(target)

    if kwargs['all']:
        _, variables = partition(lambda var: var.type == 'IDS-variable',
                                 var_lookup.values())
        variables = list(variables)
    else:
        variables = [var_lookup[name] for name in cfg.merge.variables]

    merge_data(handles, target, variables)
