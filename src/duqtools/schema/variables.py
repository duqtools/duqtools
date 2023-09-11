from typing import Union

from ._basemodel import RootModel
from ._variable import IDS2JettoVariableModel, IDSVariableModel, JettoVariableModel


class VariableConfigModel(RootModel):
    root: list[Union[JettoVariableModel, IDSVariableModel,
                     IDS2JettoVariableModel]]

    def __iter__(self):
        yield from self.root

    def __getitem__(self, index: int):
        return self.root[index]

    def to_variable_dict(self) -> dict:
        """Return dict of variables."""
        return {variable.name: variable for variable in self}
