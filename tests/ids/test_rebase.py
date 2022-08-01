from pathlib import Path

import pandas as pd
import pytest

from duqtools.ids import rebase_on_grid, rebase_on_time


@pytest.fixture
def data_set():
    fn = Path(__file__).parent / 'rebase_data.csv'
    return pd.read_csv(fn)


@pytest.fixture
def expected_out_time():
    fn = Path(__file__).parent / 'rebase_data_out_time.csv'
    return pd.read_csv(fn)


@pytest.fixture
def expected_out_ids():
    fn = Path(__file__).parent / 'rebase_data_out_ids.csv'
    return pd.read_csv(fn)


def test_rebase_on_grid(data_set, expected_out_ids):
    x_val = 'x'
    y_vals = ('y1', 'y2')
    out = rebase_on_grid(source=data_set, grid=x_val, cols=y_vals)
    pd.testing.assert_frame_equal(out, expected_out_ids)


def test_rebase_on_time(data_set, expected_out_time):
    x_val = 'x'
    y_vals = ('y1', 'y2')
    out = rebase_on_time(source=data_set, cols=[x_val, *y_vals])

    pd.testing.assert_frame_equal(out, expected_out_time)


def test_commutativity(data_set):
    x_val = 'x'
    y_vals = ('y1', 'y2')

    data_order1 = rebase_on_grid(source=rebase_on_time(source=data_set,
                                                       cols=[x_val, *y_vals]),
                                 grid=x_val,
                                 cols=y_vals)

    data_order2 = rebase_on_time(source=rebase_on_grid(source=data_set,
                                                       grid=x_val,
                                                       cols=y_vals),
                                 cols=[x_val, *y_vals])

    pd.testing.assert_frame_equal(data_order1, data_order2)
