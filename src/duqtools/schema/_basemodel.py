from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Extra
from pydantic import RootModel as PydanticRootModel


class BaseModel(PydanticBaseModel):
    """Base model."""

    model_config = ConfigDict(extra=Extra.forbid)


class RootModel(PydanticRootModel):
    """Root model."""
