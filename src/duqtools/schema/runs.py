from __future__ import annotations

from typing import List, Union

from pydantic import DirectoryPath, Field

from ._basemodel import BaseModel
from ._dimensions import IDSOperation, JettoOperation
from ._imas import ImasBaseModel


class Run(BaseModel):
    dirname: DirectoryPath = Field(None, description='Directory of run')
    data_in: ImasBaseModel
    data_out: ImasBaseModel
    operations: List[Union[IDSOperation, JettoOperation,
                           List[Union[IDSOperation, JettoOperation]]]]


class Runs(BaseModel):
    __root__: List[Run] = []

    def __iter__(self):
        yield from self.__root__

    def __getitem__(self, index: int):
        return self.__root__[index]
