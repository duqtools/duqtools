import numpy as np
import pytest

from duqtools.api import IDSMapping
from duqtools.schema._variable import IDS2JettoVariableModel
from duqtools.setup import Variables


@pytest.fixture
def var():

    class t0:
        time = np.array((10, 20, 30))

    class t1:
        time = np.array((40, 50, 60))

    handle = {'t0': IDSMapping(t0), 't1': IDSMapping(t1)}

    return Variables(handle=handle)


def test_pick_first(var):
    lookup = {
        'ids-t_start':
        IDS2JettoVariableModel.parse_raw("""
    name: ids-t_start
    type: IDS2jetto-variable
    paths:
      - {ids: t0, path: time/0}
      - {ids: t1, path: time/1}
    """)
    }

    var.lookup = lookup
    assert var.t_start == 10


def test_pick_second(var):
    lookup = {
        'ids-t_start':
        IDS2JettoVariableModel.parse_raw("""
    name: ids-t_start
    type: IDS2jetto-variable
    paths:
      - {ids: t0, path: does-not-exist/0}
      - {ids: t1, path: time/1}
    """)
    }

    var.lookup = lookup
    assert var.t_start == 50


def test_default(var):
    lookup = {
        'ids-t_start':
        IDS2JettoVariableModel.parse_raw("""
    name: ids-t_start
    type: IDS2jetto-variable
    paths:
      - {ids: t0, path: does-not-exist/0}
    default: 1337
    """)
    }

    var.lookup = lookup
    assert var.t_start == 1337


def test_raise(var):
    lookup = {
        'ids-t_start':
        IDS2JettoVariableModel.parse_raw("""
    name: ids-t_start
    type: IDS2jetto-variable
    paths:
      - {ids: t0, path: does-not-exist/0}
    """)
    }

    var.lookup = lookup

    with pytest.raises(AttributeError):
        var.t_start


def test_getattr(var):
    lookup = {'ids-t_start': None}

    var.lookup = lookup

    with pytest.raises(AttributeError, match='does_not_exist'):
        var.does_not_exist

    # ensure that default attribute lookup does not fail
    var.moo = 123
    assert var.moo == 123


def test_caching(var):
    lookup = {
        'ids-t_start':
        IDS2JettoVariableModel.parse_raw("""
    name: ids-t_start
    type: IDS2jetto-variable
    paths:
      - {ids: t0, path: time/0}
      - {ids: t1, path: time/1}
    """)
    }

    var.lookup = lookup
    assert not var._ids_cache

    var.t_start

    assert 't0' in var._ids_cache
    assert 't1' not in var._ids_cache
