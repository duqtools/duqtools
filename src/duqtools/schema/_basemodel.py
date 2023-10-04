from __future__ import annotations

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict
from pydantic import RootModel as PydanticRootModel


class BaseModel(PydanticBaseModel):
    """Base model."""

    model_config = ConfigDict(extra='forbid')


class RootModel(PydanticRootModel):
    """Root model."""
