from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra


class BaseModel(PydanticBaseModel):
    """Base model."""

    class Config:
        extra = Extra.forbid
