from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from pydantic import Field, model_validator

from duqtools.systems.jetto._dimensions import JettoOperation

from ..ids import ImasHandle
from ..ids._schema import ImasBaseModel
from ..schema import BaseModel, IDSOperation, RootModel


class Run(BaseModel):
    """Dataclass describing a run."""
    dirname: Path = Field(description='Directory of run')
    shortname: Optional[Path] = Field(
        None, description='Short name (`dirname.name`)')
    data_in: Optional[ImasBaseModel] = Field(None)
    data_out: Optional[ImasBaseModel] = Field(None)
    operations: Optional[list[Union[IDSOperation, JettoOperation, list[Union[
        IDSOperation, JettoOperation]]]]] = Field(None)

    @model_validator(mode='before')
    def shortname_compat(cls, root):
        # Compatibility with old runs.yaml
        if 'shortname' not in root and 'dirname' in root:
            root['shortname'] = root['dirname'].name
        return root

    def to_imas_handle(self) -> ImasHandle:
        if not self.data_out:
            raise NotImplementedError(
                'Run has no data_out, necessary for mapping')
        handle = ImasHandle.model_validate(self.data_out, from_attributes=True)
        return handle

    @classmethod
    def from_path(cls, path: Path):
        return cls(shortname=path, dirname=path.resolve())


class Runs(RootModel):
    """Dataclass describing a collection of runs."""
    root: list[Run] = []

    def __iter__(self):
        yield from self.root

    def __getitem__(self, index: int):
        return self.root[index]

    def __len__(self):
        return len(self.root)
