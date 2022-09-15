import numpy as np
import pytest
import xarray as xr
from idsmapping_sample_data import Sample

from duqtools.ids import (IDSMapping, rebase_on_grid, rebase_on_time,
                          standardize_grid, standardize_time)
from duqtools.schema import IDSVariableModel

TIME_VAR = IDSVariableModel(
    name='time',
    ids='core_profiles',
    path='time',
    dims=['time'],
)


@pytest.fixture
def variables1d():
    variables = [
        TIME_VAR,
        IDSVariableModel(
            name='xvar',
            ids='core_profiles',
            path='nested_profiles_1d/*/data/grid',
            dims=['time', 'x'],
        ),
        IDSVariableModel(
            name='yvar',
            ids='core_profiles',
            path='nested_profiles_1d/*/data/variable',
            dims=['time', 'x'],
        ),
    ]
    return variables


@pytest.fixture
def sample_dataset(variables1d):
    mapping = IDSMapping(Sample)
    ds = mapping.to_xarray(variables=variables1d)
    ds_grid = standardize_grid(ds, old_dim='x', new_dim='xvar', group='time')
    return ds_grid


@pytest.fixture
def expected_standardized():
    return xr.Dataset.from_dict({
        'coords': {
            'time': {
                'dims': ('time', ),
                'attrs': {},
                'data': [23, 24, 25]
            },
            'xvar': {
                'dims': ('xvar', ),
                'attrs': {},
                'data': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            }
        },
        'attrs': {},
        'dims': {
            'time': 3,
            'xvar': 10
        },
        'data_vars': {
            'yvar': {
                'dims': ('time', 'xvar'),
                'attrs': {},
                'data': [
                    [0.0, 1.0, 4.0, 9.0, 16.0, 25.0, 36.0, 49.0, 64.0, 81.0],
                    [0.0, 2.0, 4.0, 10.0, 16.0, 26.0, 36.0, 50.0, 64.0, 82.0],
                    [0.0, 3.0, 6.0, 9.0, 18.0, 27.0, 36.0, 51.0, 66.0, 81.0],
                ]
            }
        }
    })


@pytest.fixture
def expected_standardized_time():
    return xr.Dataset.from_dict({
        'coords': {
            'time': {
                'dims': ('time', ),
                'attrs': {},
                'data': [1, 2, 3]
            },
            'xvar': {
                'dims': ('xvar', ),
                'attrs': {},
                'data': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            }
        },
        'attrs': {},
        'dims': {
            'time': 3,
            'xvar': 10
        },
        'data_vars': {
            'yvar': {
                'dims': ('time', 'xvar'),
                'attrs': {},
                'data': [
                    [0.0, 1.0, 4.0, 9.0, 16.0, 25.0, 36.0, 49.0, 64.0, 81.0],
                    [0.0, 2.0, 4.0, 10.0, 16.0, 26.0, 36.0, 50.0, 64.0, 82.0],
                    [0.0, 3.0, 6.0, 9.0, 18.0, 27.0, 36.0, 51.0, 66.0, 81.0],
                ]
            }
        }
    })


@pytest.fixture
def expected_grid():
    return xr.Dataset.from_dict({
        'coords': {
            'time': {
                'dims': ('time', ),
                'attrs': {},
                'data': [23, 24, 25]
            },
            'xvar': {
                'dims': ('xvar', ),
                'attrs': {},
                'data': [-0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
            }
        },
        'attrs': {},
        'dims': {
            'time': 3,
            'xvar': 9
        },
        'data_vars': {
            'yvar': {
                'dims': ('time', 'xvar'),
                'attrs': {},
                'data': [
                    [-0.5, 0.0, 0.5, 1.0, 2.5, 4.0, 6.5, 9.0, 12.5],
                    [-1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 7.0, 10.0, 13.0],
                    [-1.5, 0.0, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0, 13.5],
                ]
            }
        }
    })


@pytest.fixture
def expected_time():
    return xr.Dataset.from_dict({
        'coords': {
            'xvar': {
                'dims': ('xvar', ),
                'attrs': {},
                'data': [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
            },
            'time': {
                'dims': ('time', ),
                'attrs': {},
                'data': [22.5, 23.0, 23.5, 24.0, 24.5]
            }
        },
        'attrs': {},
        'dims': {
            'time': 5,
            'xvar': 10
        },
        'data_vars': {
            'yvar': {
                'dims': ('time', 'xvar'),
                'attrs': {},
                'data': [
                    [0.0, 0.5, 4.0, 8.5, 16.0, 24.5, 36.0, 48.5, 64.0, 80.5],
                    [0.0, 1.0, 4.0, 9.0, 16.0, 25.0, 36.0, 49.0, 64.0, 81.0],
                    [0.0, 1.5, 4.0, 9.5, 16.0, 25.5, 36.0, 49.5, 64.0, 81.5],
                    [0.0, 2.0, 4.0, 10.0, 16.0, 26.0, 36.0, 50.0, 64.0, 82.0],
                    [0.0, 2.5, 5.0, 9.5, 17.0, 26.5, 36.0, 50.5, 65.0, 81.5],
                ]
            }
        }
    })


def test_standardize_grid_valid(sample_dataset, expected_standardized):
    xr.testing.assert_equal(sample_dataset, expected_standardized)


def test_standardize_time_valid(sample_dataset, expected_standardized_time):
    standardize_time(sample_dataset, start=1)
    xr.testing.assert_equal(sample_dataset, expected_standardized_time)


def test_rebase_on_grid(sample_dataset, expected_grid):
    new_xvar = np.linspace(-0.5, 3.5, 9)
    rebased = rebase_on_grid(sample_dataset,
                             coord_dim='xvar',
                             new_coords=new_xvar)
    xr.testing.assert_equal(rebased, expected_grid)


def test_rebase_on_time(sample_dataset, expected_time):
    new_xvar = np.linspace(22.5, 24.5, 5)
    rebased = rebase_on_time(sample_dataset, new_coords=new_xvar)
    xr.testing.assert_equal(rebased, expected_time)
