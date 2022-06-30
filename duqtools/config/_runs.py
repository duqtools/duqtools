from __future__ import annotations

from typing import List

import yaml
from pydantic import DirectoryPath

from duqtools.ids import IDSOperation, ImasLocation

from .._types import PathLike
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

    def __getitem__(self, index: int):
        return self.__root__[index]

    @classmethod
    def from_yaml(cls, runs_yaml: PathLike) -> Runs:
        """Load yaml file into Runs model."""
        with open(runs_yaml) as f:
            mapping = yaml.safe_load(f)
            return cls.parse_obj(mapping)
