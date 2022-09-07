from typing import List

from ..schema import BaseModel, JettoVar


class JettoConfigModel(BaseModel):
    __root__: List[JettoVar] = []

    def __iter__(self):
        yield from self.__root__

    def __getitem__(self, index: int):
        return self.__root__[index]
