from __future__ import annotations

from typing import List, Optional, Type

from pydantic import BaseModel, validator
from pydantic_yaml import YamlModelMixin
from typing_extensions import Literal


class JettoField(BaseModel):
    file: Literal['jetto.jset', 'jetto.in']
    field: str
    section: Optional[str] = None

    @validator('section')
    def section_lower(cls, v):
        return v.lower()


class JettoVar(BaseModel):
    doc: str
    name: str
    type: Type
    keys: List[JettoField]

    @validator('type', pre=True)
    def validate_type(cls, v):
        return {
            'str': str,
            'int': int,
            'float': float,
        }[v]


class JettoConfigModel(YamlModelMixin, BaseModel):
    __root__: List[JettoVar] = []

    def __iter__(self):
        yield from self.__root__

    def __getitem__(self, index: int):
        return self.__root__[index]
