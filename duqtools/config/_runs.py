from __future__ import annotations

from typing import List

from pydantic import DirectoryPath

from duqtools.ids import IDSOperation, ImasLocation

from .basemodel import BaseModel


class Run(BaseModel):
    dirname: DirectoryPath
    data_in: ImasLocation
    data_out: ImasLocation
    operations: List[IDSOperation]


class Runs(BaseModel):
    __root__: List[Run] = []

    def __iter__(self):
        yield from self.__root__
