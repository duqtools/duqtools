from __future__ import annotations

from getpass import getuser

from . import BaseModel


class ImasBaseModel(BaseModel):
    user: str = getuser()
    db: str
    shot: int
    run: int
