from __future__ import annotations

from typing import List

from pydantic import DirectoryPath

from duqtools.config.basemodel import BaseModel
from duqtools.ids import IDSOperation, ImasLocation


class Run(BaseModel):
    dirname: DirectoryPath
    data: ImasLocation
    operations: List[IDSOperation]


class Runs(BaseModel):
    __root__: List[Run] = []

    def __iter__(self):
        yield from self.__root__
