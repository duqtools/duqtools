from __future__ import annotations

from collections import abc
from functools import singledispatch
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from imas2xarray import Variable

from .ids._apply_model import _apply_ids
from .schema import IDSOperation
from .systems.base_system import AbstractSystem
from .systems.jetto import BaseJettoSystem
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


def get_input_var(input_variables: list[str],
                  ids_mapping,
                  system: Optional[AbstractSystem] = None,
                  run_dir: Optional[Path] = None) -> SimpleNamespace:
    """get_input_var translates a list of input variables to their values,
    which can then be used in operations.

    Parameters
    ----------
    input_variables : list[str]
        input_variables to get values for
    ids_mapping :
        ids_mapping
    system : Optional[AbstractSystem]
        system
    run_dir : Optional[Path]
        run_dir

    Returns
    -------
    a dict with all the values for the list of input variables
    """
    if system is None:
        return SimpleNamespace()

    from duqtools.config import var_lookup
    input_var = {}

    for var_name in input_variables:
        variable = var_lookup[var_name]
        if isinstance(variable, Variable):
            val = ids_mapping[variable.path]
            input_var[var_name] = val
        elif hasattr(
                system, 'get_variable'
        ):  # Must be a system variable, assume its the current system
            val = system.get_variable(run=run_dir,
                                      key=var_name,
                                      variable=variable)
            input_var[var_name] = val
        else:
            raise ValueError
    return SimpleNamespace(**input_var)


@apply_model.register
def _apply_model_ids_operation(model: IDSOperation,
                               *,
                               ids_mapping,
                               system: Optional[AbstractSystem] = None,
                               run_dir: Optional[Path] = None,
                               **kwargs):
    if model.input_variables is not None:
        kwargs['input_var'] = get_input_var(model.input_variables, ids_mapping,
                                            system, run_dir)

    _apply_ids(model, ids_mapping=ids_mapping, **kwargs)


@apply_model.register
def _apply_model_jetto_operation(
    model: JettoOperation,
    *,
    ids_mapping,
    run_dir: Path,
    system: BaseJettoSystem,
    **kwargs,
):
    if model.input_variables is not None:
        kwargs['input_var'] = get_input_var(model.input_variables, ids_mapping,
                                            system, run_dir)
    system.set_jetto_variable(run=run_dir,
                              key=model.variable.name,
                              value=model.value,
                              variable=model.variable.lookup,
                              operation=model,
                              **kwargs)
