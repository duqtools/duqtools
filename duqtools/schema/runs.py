from __future__ import annotations

from typing import List, Union

from pydantic import DirectoryPath, Field

from ..ids.handler import ImasHandle
from .basemodel import BaseModel
from .dimensions import IDSOperation, IDSSampler


class Run(BaseModel):
    dirname: DirectoryPath = Field(None, description='Directory of run')
    data_in: ImasHandle
    data_out: ImasHandle
    operations: List[Union[IDSOperation, IDSSampler]]


class Runs(BaseModel):
    __root__: List[Run] = []

    def __iter__(self):
        yield from self.__root__

    def __getitem__(self, index: int):
        return self.__root__[index]
