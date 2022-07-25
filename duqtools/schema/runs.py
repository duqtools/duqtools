from __future__ import annotations

from typing import List

from pydantic import DirectoryPath, Field

from ._basemodel import BaseModel
from ._dimensions import IDSOperation
from ._imas import ImasBaseModel


class Run(BaseModel):
    dirname: DirectoryPath = Field(None, description='Directory of run')
    data_in: ImasBaseModel
    data_out: ImasBaseModel
    operations: List[IDSOperation]


class Runs(BaseModel):
    __root__: List[Run] = []

    def __iter__(self):
        yield from self.__root__

    def __getitem__(self, index: int):
        return self.__root__[index]
