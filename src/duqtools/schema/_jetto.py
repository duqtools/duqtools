from __future__ import annotations

from typing import List, Union

from pydantic import Field, validator
from typing_extensions import Annotated, Literal

from ._basemodel import BaseModel
from ._description_helpers import formatter as f


class JsetField(BaseModel):
    file: Literal['jetto.jset'] = Field('jetto.jset')
    field: str = Field('EquilEscoRefPanel.refMajorRadius')


class NamelistField(BaseModel):
    file: Literal['jetto.in'] = Field('jetto.in')
    field: str = Field('RMJ')
    section: str = Field('NLIST1')

    @validator('section')
    def section_lower(cls, v):
        return v.lower()


JettoField = Annotated[Union[JsetField, NamelistField],
                       Field(discriminator='file')]


class JettoVar(BaseModel):
    doc: str = Field('Reference major radius (R0)')
    name: str = Field('major_radius')
    type: Literal['str', 'int', 'float'] = Field('float')
    keys: List[JettoField] = Field(
        [JsetField(), NamelistField()],
        description=f(
            """keys to update when this jetto variable is requested"""))

    def get_type(self):
        return {
            'str': str,
            'int': int,
            'float': float,
        }[self.type]
