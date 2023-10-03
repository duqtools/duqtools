from __future__ import annotations

from collections import abc
from functools import singledispatch
from pathlib import Path

from .ids._apply_model import _apply_ids
from .jetto import BaseJettoSystem
from .schema import IDSOperation, JettoOperation


@singledispatch
def apply_model(
    model,
    **kwargs,
):
    """Apply operation in model to target. Data are modified in-place.

    Parameters
    ----------
    model
        The model describes the operation to apply to the data.

    Raises
    ------
    NotImplementedError
        When the model is unknown
    """
    raise NotImplementedError(f'Unknown model: {model}')


@apply_model.register
def _apply_model_coupled(
    model: abc.Iterable,
    **kwargs,
):
    for submodel in model:
        apply_model(submodel, **kwargs)


apply_model.register(IDSOperation, _apply_ids)


@apply_model.register
def _apply_model_jetto_operation(
    model: JettoOperation,
    run_dir: Path,
    system: BaseJettoSystem,
    **kwargs,
):
    system.set_jetto_variable(run_dir, model.variable.name, model.value,
                              model.variable.lookup)
