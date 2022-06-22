from typing import List

from pydantic import DirectoryPath

from ._basemodel import BaseModel

# from duqtools.ids import ImasLocation
# from ..ids import IDSOperation


class Run(BaseModel):
    dirname: DirectoryPath
    # data: ImasLocation
    # operations: List[IDSOperation]


class Runs(BaseModel):
    __root__: List[Run] = []
