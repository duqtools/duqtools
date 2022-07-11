from __future__ import annotations

from typing import List

from pydantic import DirectoryPath, Field

from duqtools.ids._location import ImasLocation

from .basemodel import BaseModel
from .create import IDSOperation


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
