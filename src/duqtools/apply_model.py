from __future__ import annotations

from collections import abc
from functools import singledispatch
from pathlib import Path

from .schema import BaseModel, JettoOperation


@singledispatch
def apply_model(model: BaseModel, **kwargs):
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
def _apply_coupled(model: abc.Iterable, **kwargs):  # type: ignore
    for submodel in model:
        apply_model(submodel, **kwargs)


from .ids._apply_model import _apply_ids  # noqa: E402, F401


@apply_model.register
def _apply_jetto(model: JettoOperation, run_dir: Path, **kwargs):
    from .system import get_system
    system = get_system()
    system.set_jetto_variable(run_dir, model.variable.name, model.value,
                              model.variable.lookup)
