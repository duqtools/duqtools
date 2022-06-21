import os
from typing import TypeVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra

PathLike = TypeVar('PathLike', str, os.PathLike)


class BaseModel(PydanticBaseModel):

    class Config:
        extra = Extra.forbid
