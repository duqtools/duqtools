from typing import Sequence

import numpy as np
import pandas as pd
import xarray as xr

from ..operations import add_to_op_queue
from ._handle import ImasHandle
from ._io import get_ids_dataframe
from ._rebase import rebase_on_grid, rebase_on_time


@add_to_op_queue('Merge', '{target}')
def merge_data(source_data: xr.Dataset, target: ImasHandle, x_var: str,
               y_vars: Sequence[str]):
    raise NotImplementedError

    variables = [x_var, *y_vars]
    data = get_ids_dataframe(source_data, variables=variables)

    if len(set(var.ids for var in variables)) != 1:
        raise ValueError('Variables must belong to same IDS')

    input_data = target.get(x_var.ids)

    # pick first time step as basis
    common_basis = input_data[x_var.path][0]

    data = rebase_on_grid(data,
                          grid=x_val,
                          cols=y_vals,
                          grid_base=common_basis)

    common_time = input_data['time']

    # Set to common time basis
    data = rebase_on_time(data, cols=[x_val, *y_vals], time_base=common_time)

    gb = data.groupby(['tstep', x_val])

    agg_funcs = ['mean', 'std']
    agg_dict = {y_val: agg_funcs for y_val in y_vals}

    merged = gb.agg(agg_dict)

    ids_mapping = target.get(ids, exclude_empty=False)

    for y_val in y_vals:
        for tstep, group in merged.groupby('tstep'):

            mean = np.array(group[y_val, 'mean'])
            stdev = np.array(group[y_val, 'std'])

            key = f'{prefix}/{tstep}/{y_val}'

            ids_mapping[key] = mean
            ids_mapping[key + '_error_upper'] = mean + stdev

    ids_mapping.sync(target)
