from __future__ import annotations

import logging

from duqtools.config import var_lookup

from .config import cfg
from .ids import ImasHandle, merge_data, rebase_all_coords, squash_placeholders
from .utils import groupby, partition, read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def merge(**kwargs):
    """Merge data."""
    template = ImasHandle.parse_obj(cfg.merge.template)
    target = ImasHandle.parse_obj(cfg.merge.output)

    handles = read_imas_handles_from_file(cfg.merge.data)

    debug('Merge input: %s', template)
    debug('Merge output: %s', target)

    template.copy_data_to(target)

    for step in cfg.merge.plan:
        merge_data(source_data=handles,
                   target=target,
                   time_var=step.time_variable,
                   grid_var=step.grid_variable,
                   data_vars=step.data_variables)


def merge_all(**kwargs):
    """Merge as many data as possible."""

    handles = read_imas_handles_from_file(cfg.merge.data)

    # Get all known variables per ids
    _, ids_variables = partition(lambda var: var.type == 'IDS-variable',
                                 var_lookup.values())
    grouped_ids_vars = groupby(ids_variables, keyfunc=lambda var: var.ids)

    # Get all data, and rebase it
    for ids_name, variables in grouped_ids_vars.items():
        idss = [handle.get(ids_name) for handle in handles.values()]

        ids_data = [
            ids.to_xarray(
                variables=variables,
                empty_var_ok=True,
            ) for ids in idss
        ]
        ids_data = [squash_placeholders(data) for data in ids_data]

        ids_data = rebase_all_coords(ids_data, ids_data[0])

        # Now we have to squash it and write it to the target IDS
