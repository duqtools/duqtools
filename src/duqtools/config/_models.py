from __future__ import annotations

from typing import Union

from imas2xarray import VariableConfigModel

from duqtools.systems.jetto import IDS2JettoVariableModel, JettoVariableModel


class DuqtoolsVariableConfigModel(VariableConfigModel):
    root: list[Union[JettoVariableModel, IDS2JettoVariableModel]]
