from __future__ import annotations

import numpy as np
import pytest
from imas2xarray import Variable

from duqtools.apply_model import apply_model
from duqtools.ids import IDSMapping
from duqtools.schema import IDSOperation

assert_equal = np.testing.assert_array_equal


def gen_sample_data():

    class t0:
        x = np.array((10., 20., 30.))
        x_error_upper = np.array((11., 22., 33.))
        x_error_lower = np.array((8., 16., 24.))

        y = np.array((100., 200., 300.))
        y_error_upper = np.array((110., 220., 330.))

    class Data:
        data = [
            t0,
        ]
        time = np.array((0, ))

    return IDSMapping(Data)


def get_test_var(path):
    return Variable(
        name='var',
        path=path,
        ids='test',
        dims=[],
    )


TEST_INPUT = (
    {
        'operator': 'add',
        'variable': get_test_var('data/0/x'),
        'value': 2,
    },
    {
        'operator': 'multiply',
        'variable': get_test_var('data/0/y'),
        'value': 0.5,
    },
    {
        'operator': 'add',
        'variable': get_test_var('data/0/y'),
        'value': 0.5,
        'scale_to_error': True,
    },
    {
        'operator': 'add',
        'variable': get_test_var('data/0/y'),
        'value': -0.5,
        'scale_to_error': True,
    },
    {
        'operator': 'add',
        'variable': get_test_var('data/0/x'),
        'value': 3.0,
        'scale_to_error': True,
    },
    {
        'operator': 'add',
        'variable': get_test_var('data/0/x'),
        'value': -3.0,
        'scale_to_error': True,
    },
    {
        'operator': 'multiply',
        'variable': get_test_var('data/0/x'),
        'value': 1.0,
        'clip_min': 20,
    },
    {
        'operator': 'multiply',
        'variable': get_test_var('data/0/x'),
        'value': 1.0,
        'clip_max': 20,
    },
    {
        'operator': 'add',
        'variable': get_test_var('data/0/x'),
        'value': 1.0,
        'linear_ramp': (1, 2),
    },
    {
        'operator': 'add',
        'variable': get_test_var('data/0/x'),
        'value': 1.0,
        'linear_ramp': (100, 0),
    },
    {
        'operator': 'add',
        'variable': get_test_var('data/0/x'),
        'value': 1.0,
        'linear_ramp': (1, 1),
    },
    # custom
    {
        'operator': 'custom',
        'variable': get_test_var('data/0/x'),
        'value': 2.0,
        'custom_code': 'data * value',
    },
    {
        'operator': 'custom',
        'variable': get_test_var('data/0/x'),
        'value': 2.0,
        'custom_code': 'data**value',
    },
    {
        'operator': 'custom',
        'variable': get_test_var('data/0/x'),
        'value': 2.0,
        'custom_code': 'np.arange(3) * value',
    },
)

TEST_OUTPUT = (
    (12, 22, 32),
    (50, 100, 150),
    (105, 210, 315),
    (95, 190, 285),
    (13, 26, 39),
    (4, 8, 12),
    (20, 20, 30),
    (10, 20, 20),
    (11, 21.5, 32),
    (110, 70, 30),
    (11, 21, 31),
    # custom
    (20, 40, 60),
    (100, 400, 900),
    (0, 2, 4),
)


@pytest.mark.parametrize('model,output', zip(TEST_INPUT, TEST_OUTPUT))
def test_apply_model(model, output):
    data = gen_sample_data()
    model = IDSOperation(**model)

    apply_model(model, ids_mapping=data)

    assert_equal(data[model.variable.path], output)
