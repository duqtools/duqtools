from pathlib import Path

import xarray as xr

from duqtools.plot import create_chart
from duqtools.schema import IDSVariableModel

y_var = IDSVariableModel(type='IDS-variable',
                         name='t_i_ave',
                         ids='core_profiles',
                         path='profiles_1d/*/t_i_ave',
                         dims=['time', 'x'])
x_var = IDSVariableModel(type='IDS-variable',
                         name='rho_tor_norm',
                         ids='core_profiles',
                         path='profiles_1d/*/grid/rho_tor_norm',
                         dims=['time', 'x'])

dataset = xr.Dataset.from_dict({
    'coords': {},
    'attrs': {},
    'dims': {
        'run': 1,
        'time': 2,
        'x': 5
    },
    'data_vars': {
        'grid/rho_tor_norm': {
            'dims': ('run', 'time', 'x'),
            'attrs': {},
            'data': [[[0.005, 0.015, 0.025, 0.035, 0.045],
                      [0.005, 0.015, 0.025, 0.035, 0.045]]]
        },
        't_i_ave': {
            'dims': ('run', 'time', 'x'),
            'attrs': {},
            'data': [[[11225, 11218, 11205, 11184, 11156],
                      [9778, 9769, 9747, 9712, 9662]]]
        }
    }
})

extensions = ('html', )


def test_create_chart():
    create_chart(0, x_var, y_var, dataset, extensions)
    assert (Path('./chart_0.html').exists())
