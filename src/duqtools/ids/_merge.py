import logging
from typing import Sequence

import xarray as xr

from ..config import var_lookup
from ..operations import add_to_op_queue
from ..schema import IDSVariableModel
from ..utils import groupby
from ._handle import ImasHandle
from ._rebase import rebase_all_coords, squash_placeholders

logger = logging.getLogger(__name__)

info = logger.info


@add_to_op_queue('Merging to', '{target}')
def merge_data(
    handles: Sequence[ImasHandle],
    target: ImasHandle,
    variables: list[IDSVariableModel],
    callback=None,
):
    """merge_data merges the data from the handles to the target, only merges
    over the listed variables, coordination variables are never overwritten,
    and data is rebased according to the target coordination variable.

    Parameters
    ----------
    handles : Sequence[ImasHandle]
        handles
    target : ImasHandle
        target
    variables : Sequence[IDSVariableModel]
        variables
    """
    # Add dimensions to variables
    variable_dict = {}

    for variable in variables:
        variable_dict[variable.name] = variable

        for dim in variable.dims:
            try:
                dim_var = var_lookup[dim]
                variable_dict.setdefault(dim_var.name, dim_var)
            except KeyError:
                # skip dimensions without coordinates like `ion`
                pass

    variables = tuple(variable_dict.values())

    # Get all known variables per ids
    grouped_ids_vars = groupby(variables, keyfunc=lambda var: var.ids)

    i_tot = len(grouped_ids_vars)

    for i, (ids_name, ids_vars) in enumerate(grouped_ids_vars.items()):
        if callback:
            callback(i / i_tot)

        # Get all data, and rebase it
        target_ids = target.get(ids_name)  # type: ignore

        # Do not rebase to target if the target is empty
        if not target_ids:
            info('target %s:%s contains no data, skipping', target, ids_name)
            continue

        target_data = target_ids.to_xarray(variables=ids_vars,
                                           empty_var_ok=True)
        target_data = squash_placeholders(target_data)

        ids_data = [
            handle.get_variables(ids_vars, empty_var_ok=True)  # type: ignore
            for handle in handles
        ]

        ids_data = rebase_all_coords(ids_data, target_data)
        ids_data = xr.concat(ids_data, 'handle')

        # Now we have to get the stddeviations
        mean_data = ids_data.mean(dim='handle')
        std_data = ids_data.std(dim='handle', skipna=True)

        # Then, write it back to target
        for name in ids_data.data_vars.keys():
            path = variable_dict[name].path
            target_ids.write_array_in_parts(path, mean_data[name])

            path_upper = path + '_error_upper'
            target_ids.write_array_in_parts(path_upper, std_data[name])

        target_ids.sync(target)
