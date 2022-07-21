import numpy as np
import pytest

from duqtools.ids import IDSMapping, apply_model
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


TEST_INPUT = (
    {
        'operator': 'add',
        'ids': 'data/0/x',
        'value': 2,
    },
    {
        'operator': 'multiply',
        'ids': 'data/0/y',
        'value': 0.5,
    },
    {
        'operator': 'add',
        'ids': 'data/0/y',
        'value': 0.5,
        'scale_to_error': True,
    },
    {
        'operator': 'add',
        'ids': 'data/0/y',
        'value': -0.5,
        'scale_to_error': True,
    },
    {
        'operator': 'add',
        'ids': 'data/0/x',
        'value': 3.0,
        'scale_to_error': True,
    },
    {
        'operator': 'add',
        'ids': 'data/0/x',
        'value': -3.0,
        'scale_to_error': True,
    },
)

TEST_OUTPUT = (
    (12, 22, 32),
    (50, 100, 150),
    (105, 210, 315),
    (95, 190, 285),
    (13, 26, 39),
    (4, 8, 12),
)


@pytest.mark.parametrize('model,output', zip(TEST_INPUT, TEST_OUTPUT))
def test_apply_model(model, output):
    data = gen_sample_data()
    model = IDSOperation(**model)

    apply_model(model, data)

    assert_equal(data[model.ids], output)
