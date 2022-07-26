from __future__ import annotations

from getpass import getuser

from pydantic import Field, validator

from ._basemodel import BaseModel


class ImasBaseModel(BaseModel):
    """This model describes an IMAS data location."""
    user: str = Field(None, description='Username.')
    db: str = Field(None, description='IMAS db/machine name.')
    shot: int = Field(None, description='IMAS Shot number.')
    run: int = Field(None, description='IMAS Run number.')

    @validator('user', pre=True, always=True)
    def validate_user(cls, v):
        return v or getuser()
