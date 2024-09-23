from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Sequence

from .config import var_lookup
from .ids import ImasHandle, merge_data
from .operations import op_queue
from .utils import read_imas_handles_from_file

if TYPE_CHECKING:
    from imas2xarray import Variable

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def _resolve_variables(var_names: Sequence[str]) -> Sequence[Variable]:
    """Looks up variables if specified, if empty return all variables."""
    idsvar_lookup = var_lookup.filter_type('IDS-variable')

    if not var_names:
        variables = list(idsvar_lookup.values())
        op_queue.info(description='Merging all known variables')
    else:
        variables = list(idsvar_lookup[name] for name in var_names)
        for variable in variables:
            op_queue.info(description='Variable for merge',
                          extra_description=f'{variable.name}')

    return variables


def _merge(*,
           handles: Sequence[ImasHandle],
           template: ImasHandle,
           target: ImasHandle,
           variables: Sequence[Variable],
           force: bool = False):
    """Merge mas data.

    Parameters
    ----------
    handles : Sequence[ImasHandle]
        These are the imas handles that will be merged.
    template : ImasHandle
        This handle is the template that is used for the new data.
    target : ImasHandle
        This handle is the target location where the merged data will be stored.
    variables : Sequence[Variable
        These are the IDS variables to be merged.
    force : bool
        Force overwriting existing files.
    """
    for handle in handles:
        logger.debug('Source for merge %s', handle)

    op_queue.info(description='Template for merge',
                  extra_description=f'{template}')

    if target.exists() and not force:
        op_queue.add_no_op(description='Abort merge',
                           extra_description=f'{target} already exists, '
                           'use --force to overwrite')
        return

    template.copy_data_to(target)

    merge_data(handles, target, variables)


def merge(*, target: str, template: str, handles: list[str],
          input_files: list[str], var_names: list[str], force: bool, **kwargs):
    """Merge as many data as possible."""
    template = ImasHandle.from_string(template)
    target = ImasHandle.from_string(target)

    handles = [ImasHandle.from_string(handle) for handle in handles]
    for file in input_files:
        handles = handles + list(read_imas_handles_from_file(file).values())

    handles = list(set(handles))  # Remove duplicate handles

    variables = _resolve_variables(var_names)

    _merge(
        handles=handles,  # type: ignore
        template=template,  # type: ignore
        target=target,  # type: ignore
        variables=variables,
        force=force,
    )
