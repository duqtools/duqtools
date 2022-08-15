from typing import List

from ._basemodel import BaseModel


class VariableModel(BaseModel):
    """Variable for describing data within a IMAS database."""
    name: str
    ids: str
    path: str
    dims: List[str]
