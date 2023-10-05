from __future__ import annotations

from duqtools.schema import ARange, LinSpace


def test_linspace():
    model = LinSpace(start=0, stop=10, num=6)
    assert model.values == [0, 2, 4, 6, 8, 10]


def test_arange():
    model = ARange(start=0, stop=10, step=2)
    assert model.values == [0, 2, 4, 6, 8]
