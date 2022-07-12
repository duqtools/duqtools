from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra
from pydantic_yaml import YamlModelMixin


class BaseModel(YamlModelMixin, PydanticBaseModel):
    """Base model."""

    class Config:
        extra = Extra.forbid
