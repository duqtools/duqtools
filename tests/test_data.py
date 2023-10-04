from __future__ import annotations

from pytest import TEST_DATA

from duqtools.api import ImasHandle
from duqtools.utils import read_imas_handles_from_file


def _check_data_csv(data_csv: str, length: int):
    ret = read_imas_handles_from_file(data_csv)
    assert isinstance(ret, dict)
    assert len(ret.keys()) == length
    assert all(isinstance(field, str) for field in ret)
    assert all(isinstance(handle, ImasHandle) for handle in ret.values())
    return ret


def test_data_csv_4_col():
    data = TEST_DATA / 'data_4_col.csv'
    _check_data_csv(data, length=10)


def test_data_csv_5_col():
    data = TEST_DATA / 'data_5_col.csv'
    _check_data_csv(data, length=25)
