from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field, validator

from ._basemodel import BaseModel
from ._description_helpers import formatter as f


class JsetField(BaseModel):
    file: Literal['jetto.jset'] = Field('jetto.jset',
                                        description='Name of the file.')
    field: str = Field(description='Field name.')


class NamelistField(BaseModel):
    file: Literal['jetto.in'] = Field('jetto.in',
                                      description='Name of the file.')
    field: str = Field(description='Field name.')
    section: str = Field(description='Section in the config.')

    @validator('section')
    def section_lower(cls, v):
        return v.lower()


JettoField = Annotated[Union[JsetField, NamelistField],
                       Field(discriminator='file')]


class JettoVar(BaseModel):
    """These describe the jetto variables."""
    doc: str = Field(description='Docstring for the variable.')
    name: str = Field(description='Name of the variable.')
    type: Literal['str', 'int', 'float'] = Field(
        description=f('Type of the variable (str, int, float)'))
    keys: list[JettoField] = Field(description=f(
        'Jetto keys to update when this jetto variable is requested'))

    def get_type(self):
        return {
            'str': str,
            'int': int,
            'float': float,
        }[self.type]
