from typing import Sequence

import numpy as np

from ..operations import add_to_op_queue
from ..schema import VariableModel
from ._handle import ImasHandle
from ._io import get_ids_dataframe
from ._rebase import rebase_on_grid, rebase_on_time


@add_to_op_queue('Merge', '{target}')
def merge_data(source_data: Sequence[ImasHandle], target: ImasHandle,
               x_var: VariableModel, y_vars: Sequence[VariableModel]):
    variables = [x_var, *y_vars]

    if len(set(var.ids for var in variables)) != 1:
        raise ValueError('Variables must belong to same IDS')

    data = get_ids_dataframe(source_data, variables=variables)

    input_data = target.get(x_var.ids)

    # pick first time step as basis
    common_basis = input_data.get_with_replace(x_var.path, time=0)

    x_val = x_var.name
    y_vals = [var.name for var in y_vars if var.name != 'time']

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

    ids_mapping = target.get(x_var.ids, exclude_empty=False)

    for y_val in y_vals:
        var = [var for var in y_vars if var.name == y_val][0]
        for tstep, group in merged.groupby('tstep'):

            mean = np.array(group[y_val, 'mean'])
            stdev = np.array(group[y_val, 'std'])

            path = var.path.replace('$time', str(tstep))

            ids_mapping[path] = mean
            ids_mapping[path + '_error_upper'] = mean + stdev

    ids_mapping.sync(target)
