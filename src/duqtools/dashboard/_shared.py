from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Sequence

import streamlit as st
import xarray as xr

from duqtools.api import ImasHandle, standardize_grid_and_time
from duqtools.config import var_lookup
from duqtools.ids._mapping import EmptyVarError

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files

data_directory = files('duqtools.data')

try:
    default_workdir = sys.argv[1]
except IndexError:
    default_workdir = str(Path.cwd())

PREFIX = 'profiles_1d/*'
PREFIX0 = 'profiles_1d/0'


@st.cache_data
def get_ids_options():
    return tuple(var_lookup.filter_type('IDS-variable').keys())


@st.cache_data
def get_var_options(ids):
    return list(var_lookup.filter_ids(ids).values())


@st.cache_data
def get_variables(*, ids: str, x_key: str, y_keys: Sequence[str]):
    return {
        'time_var': 'time',
        'grid_var': x_key,
        'data_vars': y_keys,
    }


@st.cache_data
def _get_dataset(handles, variable, *, include_error: bool = False):
    data_var = variable['name']
    time_var = variable['dims'][0]
    grid_var = variable['dims'][1]
    variables = [data_var, time_var, grid_var]

    datasets = []

    if include_error:
        variables.append(var_lookup.error_upper(data_var))

    runs = []

    for name, handle in handles.items():
        handle = ImasHandle(**handle)

        try:
            ds = handle.get_variables(variables=variables)
        except EmptyVarError as e:
            st.warning(f'Skipping {handle}, {e}.')
            continue

        runs.append(name)

        datasets.append(ds)

    grid_var_norm = str(var_lookup.normalize(grid_var))
    time_var_norm = str(var_lookup.normalize(time_var))

    datasets = standardize_grid_and_time(
        datasets,
        grid_var=grid_var_norm,
        time_var=time_var_norm,
    )

    dataset = xr.concat(datasets, 'run')
    dataset['run'] = runs

    return dataset, time_var_norm, grid_var_norm, data_var


def get_dataset(handles, variable, *, include_error: bool = False):
    """Convert to hashable types before calling `_get_dataset`."""
    handles = {name: handle.model_dump() for name, handle in handles.items()}
    variable = variable.model_dump()

    return _get_dataset(handles, variable, include_error=include_error)


@st.cache_data
def get_base64_of_bin_file(png_file):
    with open(png_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def build_markup_for_logo(
    png_file,
    background_position='50% 10%',
    margin_top='10%',
    image_width='60%',
    image_height='',
):
    binary_string = get_base64_of_bin_file(png_file)
    return f"""
            <style>
                [data-testid="stSidebarNav"] {{
                    background-image: url("data:image/png;base64,{binary_string}");
                    background-repeat: no-repeat;
                    background-position: {background_position};
                    margin-top: {margin_top};
                    background-size: {image_width} {image_height};
                }}
            </style>
            """


def add_sidebar_logo():
    """Based on: https://stackoverflow.com/a/73278825."""
    png_file = data_directory / 'logo.png'
    logo_markup = build_markup_for_logo(png_file)
    st.markdown(
        logo_markup,
        unsafe_allow_html=True,
    )
