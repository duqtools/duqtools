from __future__ import annotations

from typing import Union

from imas2xarray import Variable, VariableConfigModel

from duqtools.systems.jetto import IDS2JettoVariableModel, JettoVariableModel


class DuqtoolsVariableConfigModel(VariableConfigModel):
    root: list[Union[  # type: ignore
        JettoVariableModel, Variable, IDS2JettoVariableModel]]
