from __future__ import annotations

import pytest

from duqtools.schema import CoupledDim, IDSOperation, Operation, OperationDim
from duqtools.systems.jetto import JettoOperation


def test_coupled_dim():
    op1 = OperationDim(variable='t_start', values=(1, 2))
    op2 = OperationDim(variable='t_e', values=(3, 4))
    model = CoupledDim([op1, op2])
    groups = model.expand()

    assert len(groups) == 2

    for group in groups:
        assert len(group) == 2
        assert isinstance(group[0], JettoOperation)
        assert isinstance(group[1], IDSOperation)


def test_operation_ids():
    model = Operation(variable='t_e', value=1.0)
    new = model.convert()
    assert isinstance(new, IDSOperation)


def test_operation_jetto():
    model = Operation(variable='t_start', value=1.0)
    new = model.convert()
    assert isinstance(new, JettoOperation)


def test_operation_fail():
    model = Operation(variable='fail', value=1.0)
    with pytest.raises(KeyError):
        model.convert()
