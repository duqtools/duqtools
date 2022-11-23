from typing import Dict, Sequence

import xarray as xr

from ..config import var_lookup
from ..operations import add_to_op_queue
from ..schema import IDSVariableModel
from ._handle import ImasHandle
from ._rebase import rebase_on_grid, rebase_on_time


def raise_if_ids_inconsistent(*variables: IDSVariableModel):
    idss = {var.ids for var in variables}
    if len(idss) != 1:
        raise ValueError('Variables must have the same IDS, '
                         f'got {len(idss)} different values: {idss}')


@add_to_op_queue('Merge', '{target}')
def queue_merge_data(*args, **kwargs):
    """Queued version of `merge_data()`."""
    return merge_data(*args, **kwargs)


def merge_data(
    source_data: Dict[str, ImasHandle],
    target: ImasHandle,
    time_var: str,
    grid_var: str,
    data_vars: Sequence[str],
):
    time_var = var_lookup[time_var]
    grid_var = var_lookup[grid_var]
    data_vars = [var_lookup[data_var] for data_var in data_vars]

    raise_if_ids_inconsistent(time_var, grid_var, *data_vars)

    TIME_DIM = time_var.name
    GRID_DIM = grid_var.name
    RUN_DIM = 'run'
    ids = grid_var.ids

    variables = [time_var, grid_var, *data_vars]

    target_data_map = target.get(ids)

    grid_dim_data = target_data_map.get_at_index(grid_var, 0)
    time_dim_data = target_data_map[time_var.path]

    datasets = []
    for run, handle in source_data.items():
        ds = handle.get_variables(variables=variables)
        datasets.append(ds)

    datasets = [
        rebase_on_grid(ds, coord_dim=GRID_DIM, new_coords=grid_dim_data)
        for ds in datasets
    ]

    datasets = [
        rebase_on_time(ds, time_dim=TIME_DIM, new_coords=time_dim_data)
        for ds in datasets
    ]

    run_data = xr.concat(datasets, RUN_DIM)

    means = run_data.mean(dim=RUN_DIM)
    stdevs = run_data.std(dim=RUN_DIM)

    for var in data_vars:
        if var.name not in run_data.data_vars:
            continue

        for i, time in enumerate(run_data.time):
            mean = means.isel({TIME_DIM: i})[var.name].data
            stdev = stdevs.isel({TIME_DIM: i})[var.name].data

            target_data_map.set_at_index(var.path, value=mean, index=i)
            target_data_map.set_at_index(var.path + '_error_upper',
                                         value=mean + stdev,
                                         index=i)

    target_data_map.sync(target)
