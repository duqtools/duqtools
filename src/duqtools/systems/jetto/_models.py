from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from imas2xarray import IDSPath
from pydantic import Field, field_validator

from duqtools.schema import BaseModel
from duqtools.utils import formatter as f


class JsetField(BaseModel):
    file: Literal['jetto.jset'] = Field('jetto.jset',
                                        description='Name of the file.')
    field: str = Field(description='Field name.')


class NamelistField(BaseModel):
    file: Literal['jetto.in'] = Field('jetto.in',
                                      description='Name of the file.')
    field: str = Field(description='Field name.')
    section: str = Field(description='Section in the config.')

    @field_validator('section')
    def section_upper(cls, v):
        return v.upper()


JettoField = Annotated[Union[JsetField, NamelistField],
                       Field(discriminator='file')]


class JettoVar(BaseModel):
    """These describe the jetto variables."""
    doc: str = Field(description='Docstring for the variable.')
    name: str = Field(description='Name of the variable.')
    type: Literal['str', 'int', 'float'] = Field(
        description=f('Type of the variable (str, int, float)'))
    dimension: Optional[Literal['scalar', 'vector']] = Field(None)
    keys: list[JettoField] = Field(description=f(
        'Jetto keys to update when this jetto variable is requested'))

    def get_type(self):
        return {
            'str': str,
            'int': int,
            'float': float,
        }[self.type]


class JettoVariableModel(BaseModel):
    """Variable for describing variables specific to Jetto, The lookup table
    can be defined as a JettoVar under the lookup key."""

    type: str = Field('jetto-variable',
                      description='Discriminator for the variable type.')

    name: str = Field(description=f("""
        Name of the variable.
        Used for the lookup table to find actual fields.
        """))

    lookup: Optional[JettoVar] = Field(None,
                                       description=f("""
    Description of the fields that have to be updated for a Jetto Variable
    """))


class IDS2JettoVariableModel(BaseModel):
    """Variable for describing the relation between IDS data and jetto
    variables.

    The variable can be given a name, which can be used in the config
    template to reference the variable. It will also be used as the
    column labels or on plots.
    """
    name: str = Field(description=f("""
        Name of the variable.
        This will be used to reference this variable.
    """))
    type: str = Field('IDS2jetto-variable',
                      description='discriminator for the variable type')
    paths: list[IDSPath] = Field(description=f("""
        Search these variables in the given order until a match with the conditions
        defined below is found.
    """))
    default: Optional[float] = Field(None,
                                     description=f("""
        Default value if no match is found. Set to None to raise an exeption instead."""
                                                   ))
