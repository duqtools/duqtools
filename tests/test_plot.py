from pathlib import Path

import xarray as xr

from duqtools.plot import create_chart
from duqtools.schema import IDSVariableModel

y_var = IDSVariableModel(type='IDS-variable',
                         name='t_i_average',
                         ids='core_profiles',
                         path='profiles_1d/*/t_i_average',
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
            'data': [[[
                0.005025125628140704, 0.015075376884422112,
                0.02512562814070352, 0.035175879396984924, 0.04522613065326634
            ],
                      [
                          0.005025125628140704, 0.015075376884422112,
                          0.02512562814070352, 0.035175879396984924,
                          0.04522613065326634
                      ]]]
        },
        't_i_average': {
            'dims': ('run', 'time', 'x'),
            'attrs': {},
            'data': [[[
                11225.708271647569, 11218.849976823274, 11205.06692865499,
                11184.339034931223, 11156.59739007622
            ],
                      [
                          9778.147119233852, 9769.039410357258,
                          9747.670679121258, 9712.03100773275,
                          9662.872545139579
                      ]]]
        }
    }
})

extensions = ('html', )


def test_create_chart():
    create_chart(0, x_var, y_var, dataset, extensions)
    assert (Path('./chart_0.html').exists())
