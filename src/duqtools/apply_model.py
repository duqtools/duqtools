from __future__ import annotations

from collections import abc
from functools import singledispatch
from pathlib import Path

from .ids._apply_model import _apply_ids
from .schema import IDSOperation
from .schema.variables import IDSVariableModel
from .systems.jetto import BaseJettoSystem, JettoVariableModel
from .systems.jetto._dimensions import JettoOperation


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


@apply_model.register
def _apply_model_ids_operation(model: IDSOperation, *, ids_mapping, **kwargs):
    from duqtools.config import var_lookup
    input_var = {}
    if model.input_variables is not None:
        for var_name in model.input_variables:
            variable = var_lookup[var_name]
            if isinstance(variable, JettoVariableModel):
                pass
            elif isinstance(variable, IDSVariableModel):
                val = ids_mapping[variable.path]
                input_var[var_name] = val
            else:
                raise NotImplementedError(
                    f'{variable} convert not implemented')
    _apply_ids(model, ids_mapping=ids_mapping, input_var=input_var, **kwargs)


@apply_model.register
def _apply_model_jetto_operation(
    model: JettoOperation,
    run_dir: Path,
    system: BaseJettoSystem,
    **kwargs,
):
    system.set_jetto_variable(
        run=run_dir,
        key=model.variable.name,
        value=model.value,
        variable=model.variable.lookup,
    )
