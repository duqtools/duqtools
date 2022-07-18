from __future__ import annotations

from getpass import getuser

from .basemodel import BaseModel


class ImasModel(BaseModel):
    user: str = getuser()
    db: str
    shot: int
    run: int
