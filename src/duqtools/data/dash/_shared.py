import sys
from pathlib import Path
from typing import Sequence

import streamlit as st
import xarray as xr

from duqtools.api import ImasHandle, standardize_grid_and_time
from duqtools.config import var_lookup

try:
    default_workdir = sys.argv[1]
except IndexError:
    default_workdir = str(Path.cwd())

PREFIX = 'profiles_1d/*'
PREFIX0 = 'profiles_1d/0'


@st.experimental_memo
def get_ids_options():
    return tuple(var_lookup.filter_type('IDS-variable').keys())


@st.experimental_memo
def get_var_options(ids):
    return list(var_lookup.filter_ids(ids).values())


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
        ds = handle.get_variables(variables=variables)
        datasets.append(ds)

    datasets = standardize_grid_and_time(
        datasets,
        grid_var=grid_var,
        time_var=time_var,
    )

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
