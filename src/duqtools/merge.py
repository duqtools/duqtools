from __future__ import annotations

import logging
from typing import List, Optional

from .config import var_lookup
from .ids import ImasHandle, merge_data
from .operations import op_queue
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def merge(*, merge_all: bool, target: str, template: str, handles: List[str],
          runfile: Optional[str], variables: Optional[List[str]], **kwargs):
    """Merge as many data as possible."""
    template = ImasHandle.from_string(template)
    target = ImasHandle.from_string(target)

    handles = [ImasHandle.from_string(handle) for handle in handles]
    if runfile:
        handles = handles + list(read_imas_handles_from_file(runfile).values())

    handles = set(handles)  # Remove duplicate handles

    for handle in handles:
        op_queue.add(action=lambda: None,
                     description='Source for merge',
                     extra_description=f'{handle}')

    if merge_all:
        ids_variables = [
            var for var in var_lookup.values() if var.type == 'IDS-variable'
        ]
        op_queue.add(action=lambda: None,
                     description='Merging all known variables')
    else:
        if not variables:
            op_queue.add_no_op('No variables specified for merge',
                               'recommend to abort')
        else:
            if len(variables) == 0:
                op_queue.add_no_op('No variables specified for merge',
                                   'recommend to abort')

            ids_variables = [var_lookup[name] for name in variables]
            for variable in ids_variables:
                op_queue.add(action=lambda: None,
                             description='Variable for merge',
                             extra_description=f'{variable.name}')

    op_queue.add(action=lambda: None,
                 description='Template for merge',
                 extra_description=f'{template}')
    template.copy_data_to(target)

    merge_data(handles, target, ids_variables)
