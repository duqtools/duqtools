import numpy as np
import pytest

from duqtools.ids import IDSMapping

assert_equal = np.testing.assert_array_equal


class Sample:
    a = np.array((1, 2))

    class b:

        class c:
            d = np.array((4, 5))
            e = 'not found'

        f = [np.array((6, 7)), np.array((8, 9))]
        g = 123  # not found

    _h = np.array((0, 0))


def test_mapping():
    s = IDSMapping(Sample)

    assert_equal(s.flat_fields['a'], np.array([1, 2]))
    assert_equal(s.flat_fields['b/c/d'], np.array([4, 5]))
    assert_equal(s.flat_fields['b/f/0'], np.array([6, 7]))
    assert_equal(s.flat_fields['b/f/1'], np.array([8, 9]))
    assert_equal(s.flat_fields['_h'], np.array([0, 0]))

    assert 'b/g' not in s.flat_fields
    assert 'b/c/e' not in s.flat_fields

    assert_equal(s.fields['b']['f']['0'], np.array([6, 7]))


def test_mapping_unknown_key_fail():
    s = IDSMapping(Sample)
    with pytest.raises(KeyError):
        s.fields['this key does not exist']


def test_find_all():
    s = IDSMapping(Sample)
    d = s.findall('b/f/[0-9]')

    assert len(d) == 2
    assert 'b/f/0' in d
    assert 'b/f/1' in d


def test_find_group():
    s = IDSMapping(Sample)
    d = s.find_by_group(r'(b/f)/(\d)')

    assert len(d) == 2
    assert ('b/f', '0') in d
    assert ('b/f', '1') in d


def test_find_index():
    s = IDSMapping(Sample)
    inp = 'b/f/$i'
    d = s.find_by_index(inp)

    assert len(d) == 1
    assert inp in d
    assert_equal(d[inp][0], np.array([6, 7]))
    assert_equal(d[inp][1], np.array([8, 9]))
