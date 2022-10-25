import sys
from pathlib import Path
from typing import Sequence

import streamlit as st
import xarray as xr

from duqtools.config import var_lookup
from duqtools.ids import (ImasHandle, rebase_on_grid, rebase_on_time,
                          standardize_grid)

try:
    default_workdir = sys.argv[1]
except IndexError:
    default_workdir = str(Path.cwd())

PREFIX = 'profiles_1d/*'
PREFIX0 = 'profiles_1d/0'


@st.experimental_memo
def get_ids_options():
    options = tuple(
        {v.ids
         for v in var_lookup.values() if (v.type == 'IDS-variable')})
    return options


@st.experimental_memo
def get_var_options(ids):
    options = [
        k for k, v in var_lookup.items()
        if (v.type == 'IDS-variable') and (v.ids == ids)
    ]
    return options


@st.experimental_memo
def get_variables(*, ids: str, x_key: str, y_keys: Sequence[str]):
    return {
        'time_var': 'time',
        'grid_var': x_key,
        'data_vars': y_keys,
    }


@st.experimental_memo
def _get_dataset(handles, *, ids, time_var, grid_var, data_vars):
    datasets = []

    variables = tuple((time_var, grid_var, *data_vars))

    for name, handle in handles.items():
        handle = ImasHandle(**handle)

        data_map = handle.get(ids)

        ds = data_map.to_xarray(variables=variables)

        ds = standardize_grid(
            ds,
            new_dim=grid_var,
            old_dim='x',
            new_dim_data=0,
            group=time_var,
        )
        datasets.append(ds)

    reference_grid = datasets[0][grid_var].data

    datasets = [
        rebase_on_grid(ds, coord_dim=grid_var, new_coords=reference_grid)
        for ds in datasets
    ]

    reference_time = datasets[0][time_var].data

    datasets = [
        rebase_on_time(ds, time_dim=time_var, new_coords=reference_time)
        for ds in datasets
    ]

    dataset = xr.concat(datasets, 'run')
    dataset['run'] = list(handles.keys())

    return dataset


def get_dataset(handles, *, ids, time_var, grid_var, data_vars):
    """Convert to hashable types before calling `_get_dataset`."""
    handles = {name: handle.dict() for name, handle in handles.items()}
    return _get_dataset(handles,
                        ids=ids,
                        time_var=time_var,
                        grid_var=grid_var,
                        data_vars=data_vars)
