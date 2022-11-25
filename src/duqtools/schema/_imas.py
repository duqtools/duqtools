from __future__ import annotations

from getpass import getuser

from pydantic import Field, validator

from ._basemodel import BaseModel


class ImasBaseModel(BaseModel):
    """This model describes an IMAS data location."""
    user: str = Field(None, description='Username.')
    db: str = Field(description='IMAS db/machine name.')
    shot: int = Field(description='IMAS Shot number.')
    run: int = Field(description='IMAS Run number.')

    @validator('user', pre=True, always=True)
    def validate_user(cls, v):
        return v or getuser()

    def __hash__(self):  # Needed to compare handles
        return hash((self.user, self.db, self.shot, self.run))
