from typing import Sequence

import xarray as xr

from ..operations import add_to_op_queue
from ..schema import VariableModel
from ._handle import ImasHandle
from ._rebase import rebase_on_time, standardize_grid


def _get_placeholder_dim(grid_var: VariableModel,
                         time_var: VariableModel) -> str:
    dims = [dim for dim in grid_var.dims if dim != time_var.name]

    if len(dims) != 1:
        raise ValueError('Number of non-time dimensions must be 1.')

    return dims[0]


def raise_if_ids_inconsistent(*variables: VariableModel):
    idss = {var.ids for var in variables}
    if len(idss) != 1:
        raise ValueError('Variables must have the same IDS, '
                         f'got {len(idss)} different values: {idss}')


@add_to_op_queue('Merge', '{target}')
def merge_data(
    source_data: Sequence[ImasHandle],
    target: ImasHandle,
    time_var: VariableModel,
    grid_var: VariableModel,
    data_vars: Sequence[VariableModel],
):
    raise_if_ids_inconsistent(time_var, grid_var, *data_vars)

    TIME_DIM = time_var.name
    GRID_DIM = grid_var.name
    PLACEHOLDER_DIM = _get_placeholder_dim(grid_var, time_var)
    RUN_DIM = 'run'
    ids = grid_var.ids

    variables = [time_var, grid_var, *data_vars]

    target_data_map = target.get(ids)

    # pick first time step as basis
    GRID_DIM = grid_var.name
    grid_dim_data = target_data_map.get_with_replace(grid_var.path, time=0)
    time_dim_data = target_data_map[time_var.path]

    datasets = []
    for handle in source_data:
        data = handle.get(ids, exclude_empty=True)
        ds = data.to_xarray(variables=variables)

        ds = standardize_grid(
            ds,
            new_dim=GRID_DIM,
            old_dim=PLACEHOLDER_DIM,
            new_dim_data=grid_dim_data,
            group=TIME_DIM,
        )

        datasets.append(ds)

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

            target_data_map.set_with_replace(var.path, value=mean, time=i)
            target_data_map.set_with_replace(var.path + '_error_upper',
                                             value=mean + stdev,
                                             time=i)

    target_data_map.sync(target)
