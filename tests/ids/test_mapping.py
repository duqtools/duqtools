import numpy as np
import pytest

from duqtools.ids._mapping import IDSMapping

assert_equal = np.testing.assert_array_equal


class t0:
    x = np.array((0, 1))
    y = np.array((2, 3))
    z = 'not found'


class t1:
    x = np.array((4, 5))
    y = np.array((6, 7))
    z = 123


class t2:
    x = np.array((8, 9))
    y = np.array((10, 11))


class Sample:
    data = [t0, t1, t2]

    time = np.array((1, 2, 3))
    _h = np.array((0, 0))


def test_mapping():
    s = IDSMapping(Sample)

    assert_equal(s.flat_fields['time'], np.array([1., 2., 3.]))
    assert_equal(s.flat_fields['_h'], np.array([0, 0]))
    assert_equal(s.flat_fields['data/0/x'], np.array([0, 1]))
    assert_equal(s.flat_fields['data/0/y'], np.array([2, 3]))
    assert_equal(s.flat_fields['data/1/x'], np.array([4, 5]))
    assert_equal(s.flat_fields['data/1/y'], np.array([6, 7]))
    assert_equal(s.flat_fields['data/2/x'], np.array([8, 9]))
    assert_equal(s.flat_fields['data/2/y'], np.array([10, 11]))

    assert 'data/0/z' not in s.flat_fields
    assert 'data/0/z' not in s.flat_fields

    assert_equal(s.fields['data']['0']['x'], np.array([0, 1]))


def test_mapping_unknown_key_fail():
    s = IDSMapping(Sample)
    with pytest.raises(KeyError):
        s.fields['this key does not exist']


def test_find_all():
    s = IDSMapping(Sample)
    d = s.findall('data/[0-2]/x')

    assert len(d) == 3
    assert 'data/0/x' in d
    assert 'data/1/x' in d
    assert 'data/2/x' in d


def test_find_group():
    s = IDSMapping(Sample)
    d = s.find_by_group(r'data/(0)/(x|y)')

    assert len(d) == 2
    assert ('0', 'x') in d
    assert ('0', 'y') in d


def test_find_index():
    s = IDSMapping(Sample)
    inp = 'data/$i/x'
    d = s.find_by_index(inp)

    assert len(d) == 1
    assert inp in d
    assert_equal(d[inp][0], np.array([0, 1]))
    assert_equal(d[inp][1], np.array([4, 5]))
    assert_equal(d[inp][2], np.array([8, 9]))


def test_to_numpy():
    s = IDSMapping(Sample)
    cols, ret = s.to_numpy('x', 'y', prefix='data')

    assert cols == ('tstep', 'time', 'x', 'y')
    assert ret.shape == (6, 4)
    assert_equal(ret[:, 0], [0, 0, 1, 1, 2, 2])


def test_to_dataframe():
    s = IDSMapping(Sample)
    df = s.to_dataframe('x', 'y', prefix='data')

    assert tuple(df.columns) == ('tstep', 'time', 'x', 'y')
    assert df.shape == (6, 4)
    assert_equal(df['tstep'], [0, 0, 1, 1, 2, 2])
