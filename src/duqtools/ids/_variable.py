from typing import List

from pydantic import BaseModel


class Variable(BaseModel):
    """Variable for describing data within a IMAS database."""
    name: str
    ids: str
    path: str
    dims: List[str]
