import sys
from pathlib import Path
from typing import Sequence

import xarray as xr

from duqtools.api import ImasHandle, standardize_grid_and_time
from duqtools.config import var_lookup

try:
    from streamlit import cache_data
except ImportError:
    # work-around for streamlit<1.18
    from streamlit import experimental_memo as cache_data

try:
    default_workdir = sys.argv[1]
except IndexError:
    default_workdir = str(Path.cwd())

PREFIX = 'profiles_1d/*'
PREFIX0 = 'profiles_1d/0'


@cache_data
def get_ids_options():
    return tuple(var_lookup.filter_type('IDS-variable').keys())


@cache_data
def get_var_options(ids):
    return list(var_lookup.filter_ids(ids).values())


@cache_data
def get_variables(*, ids: str, x_key: str, y_keys: Sequence[str]):
    return {
        'time_var': 'time',
        'grid_var': x_key,
        'data_vars': y_keys,
    }


@cache_data
def _get_dataset(handles, variable, *, include_error: bool = False):
    data_var = variable['name']
    time_var = variable['dims'][0]
    grid_var = variable['dims'][1]
    variables = [data_var, time_var, grid_var]

    datasets = []

    if include_error:
        variables.append(var_lookup.error_upper(data_var))

    for name, handle in handles.items():
        handle = ImasHandle(**handle)
        ds = handle.get_variables(variables=variables)
        datasets.append(ds)

    grid_var_norm = var_lookup.normalize(grid_var)
    time_var_norm = var_lookup.normalize(time_var)

    datasets = standardize_grid_and_time(
        datasets,
        grid_var=grid_var_norm,
        time_var=time_var_norm,
    )

    dataset = xr.concat(datasets, 'run')
    dataset['run'] = list(handles.keys())

    return dataset, time_var_norm, grid_var_norm, data_var


def get_dataset(handles, variable, *, include_error: bool = False):
    """Convert to hashable types before calling `_get_dataset`."""
    handles = {name: handle.dict() for name, handle in handles.items()}
    variable = variable.dict()

    return _get_dataset(handles, variable, include_error=include_error)
