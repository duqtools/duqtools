from __future__ import annotations

from pathlib import Path
from typing import List, Union

from pydantic import Field

from ._basemodel import BaseModel
from ._dimensions import IDSOperation, JettoOperation
from ._imas import ImasBaseModel


class Run(BaseModel):
    dirname: Path = Field(description='Directory of run')
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

    def construct(run_list: List[dict]):
        __root__ = []
        for run in run_list:
            __root__.append(Run.construct(**run))
        return __root__
