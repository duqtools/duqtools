from pathlib import Path
from typing import Optional, Union

from pydantic import Field, root_validator

from ..ids import ImasHandle
from ..schema import BaseModel, IDSOperation, ImasBaseModel, JettoOperation


class Run(BaseModel):
    dirname: Path = Field(None, description='Directory of run')
    shortname: Optional[Path] = Field(
        description='Short name (`dirname.name`)')
    data_in: ImasBaseModel = Field(None)
    data_out: ImasBaseModel = Field(None)
    operations: Optional[list[Union[IDSOperation, JettoOperation,
                                    list[Union[IDSOperation,
                                               JettoOperation]]]]]

    @root_validator()
    def shortname_compat(cls, root):
        # Compatibility with old runs.yaml
        if 'shortname' not in root and 'dirname' in root:
            root['shortname'] = root['dirname'].name
        return root

    def to_imas_handle(self) -> ImasHandle:
        if not self.data_out:
            raise NotImplementedError(
                'Run has no data_out, necessary for mapping')
        handle = ImasHandle.parse_obj(self.data_out)
        return handle

    @classmethod
    def from_path(cls, path: Path):
        return cls(shortname=path, dirname=path.resolve())


class Runs(BaseModel):
    __root__: list[Run] = []

    def __iter__(self):
        yield from self.__root__

    def __getitem__(self, index: int):
        return self.__root__[index]
