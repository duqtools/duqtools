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

    assert_equal(s['time'], np.array([1., 2., 3.]))
    assert_equal(s['_h'], np.array([0, 0]))
    assert_equal(s['data/0/x'], np.array([0, 1]))
    assert_equal(s['data/0/y'], np.array([2, 3]))
    assert_equal(s['data/1/x'], np.array([4, 5]))
    assert_equal(s['data/1/y'], np.array([6, 7]))
    assert_equal(s['data/2/x'], np.array([8, 9]))
    assert_equal(s['data/2/y'], np.array([10, 11]))

    assert_equal(s['data/0/x/0'], 0)
    assert_equal(s['data/0/x/1'], 1)

    assert 'data/0/z' not in s._keys


def test_mapping_unknown_key_fail():
    s = IDSMapping(Sample)
    with pytest.raises(KeyError):
        s['this key does not exist']


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


def test_get_set_at_index():
    s = IDSMapping(Sample)
    values = np.array([111, 222])

    s.set_at_index('data/*/x', 1, values)
    assert_equal(s['data/1/x'], values)

    ret = s.get_at_index('data/*/x', 1)
    assert_equal(ret, values)


def test_length():
    s = IDSMapping(Sample)

    assert len(s) == 8
    assert s.length_of_key('data') == 3
    assert s.length_of_key('data/1/z') is None
