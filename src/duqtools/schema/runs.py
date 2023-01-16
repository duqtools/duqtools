from __future__ import annotations

from pathlib import Path
from typing import Union

from pydantic import Field, root_validator

from ._basemodel import BaseModel
from ._dimensions import IDSOperation, JettoOperation
from ._imas import ImasBaseModel


class Run(BaseModel):
    dirname: Path = Field(description='Directory of run')
    shortname: Path = Field(description='Short name (`dirname.name`)')
    data_in: ImasBaseModel
    data_out: ImasBaseModel
    operations: list[Union[IDSOperation, JettoOperation,
                           list[Union[IDSOperation, JettoOperation]]]]

    @root_validator()
    def shortname_compat(cls, root):
        # Compatibility with old runs.yaml
        if not root['shortname']:
            root['shortname'] = root['dirname'].name
        return root


class Runs(BaseModel):
    __root__: list[Run] = []

    def __iter__(self):
        yield from self.__root__

    def __getitem__(self, index: int):
        return self.__root__[index]
