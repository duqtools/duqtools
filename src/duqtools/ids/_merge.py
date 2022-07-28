from typing import List

import numpy as np
import pandas as pd

from ._get_ids_tree import get_ids_tree
from ._handle import ImasHandle
from ._mapping import IDSMapping
from ._rebase import rebase_on_ids, rebase_on_time


def merge(data: pd.DataFrame,
          template: ImasHandle,
          target: ImasHandle,
          x_val: str,
          y_vals: List[str],
          prefix: str = 'profiles_1d'):
    template_data = get_ids_tree(template)

    # pick first time step as basis
    common_basis = template_data[f'{prefix}/0/{x_val}']

    data = rebase_on_ids(data,
                         base_col=x_val,
                         value_cols=y_vals,
                         new_base=common_basis)

    common_time = template_data['time']

    # Set to common time basis
    data = rebase_on_time(data, cols=[x_val, *y_vals], new_base=common_time)

    gb = data.groupby(['tstep', x_val])

    agg_funcs = ['mean', 'std']
    agg_dict = {y_val: agg_funcs for y_val in y_vals}

    merged = gb.agg(agg_dict)

    template.copy_ids_entry_to(target)

    core_profiles = target.get('core_profiles')
    ids_mapping = IDSMapping(core_profiles, exclude_empty=False)

    for y_val in y_vals:
        for tstep, group in merged.groupby('tstep'):

            mean = np.array(group[y_val, 'mean'])
            stdev = np.array(group[y_val, 'std'])

            key = f'{prefix}/{tstep}/{y_val}'

            ids_mapping[key] = mean
            ids_mapping[key + '_error_upper'] = mean + stdev

    ids_mapping.sync(target)
