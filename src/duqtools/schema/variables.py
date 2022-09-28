from typing import List, Union

from ._basemodel import BaseModel
from ._variable import IDSVariableModel, JettoVariableModel


class VariableConfigModel(BaseModel):
    __root__: List[Union[JettoVariableModel, IDSVariableModel]]

    def __iter__(self):
        yield from self.__root__

    def __getitem__(self, index: int):
        return self.__root__[index]

    def to_variable_dict(self) -> dict:
        """Return dict of variables."""
        return {variable.name: variable for variable in self}
