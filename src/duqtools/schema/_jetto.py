from __future__ import annotations

from typing import List, Union

from pydantic import Field, validator
from typing_extensions import Annotated, Literal

from ._basemodel import BaseModel
from ._description_helpers import formatter as f


class JsetField(BaseModel):
    file: Literal['jetto.jset']
    field: str


class NamelistField(BaseModel):
    file: Literal['jetto.in']
    field: str
    section: str

    @validator('section')
    def section_lower(cls, v):
        return v.lower()


JettoField = Annotated[Union[JsetField, NamelistField],
                       Field(discriminator='file')]


class JettoVar(BaseModel):
    doc: str
    name: str
    type: Literal['str', 'int', 'float']
    keys: List[JettoField] = Field(
        f("""
    keys to update when this jetto variable is requested
    """))

    def get_type(self):
        return {
            'str': str,
            'int': int,
            'float': float,
        }[self.type]
