from __future__ import annotations

from typing import List

from pydantic import DirectoryPath, Field

from ._create import IDSOperation
from .basemodel import BaseModel
from .imaslocation import ImasLocation


class Run(BaseModel):
    dirname: DirectoryPath = Field(None, description='Directory of run')
    data_in: ImasLocation
    data_out: ImasLocation
    operations: List[IDSOperation]


class Runs(BaseModel):
    __root__: List[Run] = []

    def __iter__(self):
        yield from self.__root__

    def __getitem__(self, index: int):
        return self.__root__[index]
