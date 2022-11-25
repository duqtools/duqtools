from typing import List, Sequence

import xarray as xr

from ..config import var_lookup
from ..operations import add_to_op_queue
from ..schema import IDSVariableModel
from ..utils import groupby
from ._handle import ImasHandle
from ._rebase import rebase_all_coords, squash_placeholders


@add_to_op_queue('Merging to', '{target}')
def merge_data(
    handles: Sequence[ImasHandle],
    target: ImasHandle,
    variables: List[IDSVariableModel],
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

    # make sure we do not mess up input arguments
    variables = variables.copy()

    # Sometimes, dimensions are not yet included,
    # We can safely include them into the variables manually, as they are
    # automatically transformed into coordinates, and therefore not written back
    variable_dict = {variable.name: variable for variable in variables}
    for variable in variables:
        for dim in variable.dims:
            # TODO time should also be $ prefixed, remove the `or time` when fixed
            if not (dim.startswith('$') or dim.startswith('time')):
                continue
            name = dim.lstrip('$')
            if name not in variable_dict:
                variables.append(var_lookup[name])
                variable_dict[name] = variables[-1]

    # Get all known variables per ids
    grouped_ids_vars = groupby(variables, keyfunc=lambda var: var.ids)

    for ids_name, variables in grouped_ids_vars.items():

        # Get all data, and rebase it
        target_ids = target.get(ids_name)  # type: ignore
        target_data = target_ids.to_xarray(variables=variables,
                                           empty_var_ok=True)
        target_data = squash_placeholders(target_data)

        ids_data = [
            handle.get_variables(ids_name, empty_var_ok=True)  # type: ignore
            for handle in handles
        ]

        ids_data = rebase_all_coords(ids_data, target_data)

        ids_data = xr.concat(ids_data, 'handle')

        # Now we have to get the stddeviations
        mean_data = ids_data.mean(dim='handle')
        std_data = ids_data.std(dim='handle', skipna=True)

        # Then, write it back to target
        for name in ids_data.data_vars.keys():
            target_ids.write_array_in_parts(variable_dict[name].path,
                                            mean_data[name])
            target_ids.write_array_in_parts(
                variable_dict[name].path + '_error_upper', std_data[name])
        target_ids.sync(target)
