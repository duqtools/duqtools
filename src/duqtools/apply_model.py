from __future__ import annotations

from functools import singledispatch
from pathlib import Path

from .schema import BaseModel, JettoOperation


@singledispatch
def apply_model(model: BaseModel, **kwargs) -> None:
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


from .ids._apply_model import _apply_ids  # noqa: E402, F401


@apply_model.register
def _apply_jetto(model: JettoOperation, run_dir: Path, **kwargs) -> None:
    from .system import get_system
    system = get_system()
    system.set_jetto_variable(run_dir, model.variable.name, model.value)
