import sys
from pathlib import Path
from typing import Sequence

import streamlit as st
import xarray as xr

from duqtools.api import Variable
from duqtools.ids import (ImasHandle, rebase_on_grid, rebase_on_time,
                          standardize_grid)

try:
    default_workdir = sys.argv[1]
except IndexError:
    default_workdir = str(Path.cwd())

PREFIX = 'profiles_1d/$time'
PREFIX0 = 'profiles_1d/0'


@st.experimental_memo
def get_options(a_run, ids):
    a_profile = ImasHandle(**a_run).get(ids, exclude_empty=True)
    return sorted(a_profile.find_by_group('profiles_1d/0/(.*)').keys())


@st.experimental_memo
def get_variables(*, ids: str, x_key: str, y_keys: Sequence[str]):
    time_var = dict(
        name='time',
        ids=ids,
        path='time',
        dims=['time'],
    )

    grid_var = dict(name=x_key, ids=ids, path=f'{PREFIX}/{x_key}', dims=['x'])

    data_vars = tuple(
        dict(name=y_key, ids=ids, path=f'{PREFIX}/{y_key}', dims=['x'])
        for y_key in y_keys)

    return {
        'time_var': time_var,
        'grid_var': grid_var,
        'data_vars': data_vars,
    }


@st.experimental_memo
def _get_dataset(handles, *, time_var, grid_var, data_vars):
    datasets = []

    time_var = Variable(**time_var)
    grid_var = Variable(**grid_var)
    data_vars = tuple((Variable(**data_var) for data_var in data_vars))

    variables = tuple((time_var, grid_var, *data_vars))

    for name, handle in handles.items():
        handle = ImasHandle(**handle)

        data_map = handle.get(grid_var.ids)

        ds = data_map.to_xarray(variables=variables)

        ds = standardize_grid(
            ds,
            new_dim=grid_var.name,
            old_dim=grid_var.dims[0],
            new_dim_data=0,
            group=time_var.name,
        )
        datasets.append(ds)

    reference_grid = datasets[0][grid_var.name].data

    datasets = [
        rebase_on_grid(ds, coord_dim=grid_var.name, new_coords=reference_grid)
        for ds in datasets
    ]

    reference_time = datasets[0][time_var.name].data

    datasets = [
        rebase_on_time(ds, time_dim=time_var.name, new_coords=reference_time)
        for ds in datasets
    ]

    dataset = xr.concat(datasets, 'run')
    dataset['run'] = list(handles.keys())

    return dataset


def get_dataset(handles, *, time_var, grid_var, data_vars):
    """Convert to hashable types before calling `_get_dataset`."""
    handles = {name: handle.dict() for name, handle in handles.items()}
    return _get_dataset(handles,
                        time_var=time_var,
                        grid_var=grid_var,
                        data_vars=data_vars)
