from getpass import getuser
from pathlib import Path
from typing import List

from pydantic import DirectoryPath, Field, validator

from ._runs import Run, Runs
from .basemodel import BaseModel


class WorkDirectory(BaseModel):
    root: DirectoryPath = Field(
        f'/pfs/work/{getuser()}/jetto/runs/',
        description='The folder from which experiments have to be run,'
        ' rjettov runs relative to this folder')

    @property
    def cwd(self):
        cwd = Path.cwd()
        if not cwd.relative_to(self.root):
            raise IOError(
                f'Work directory must be a subdirectory of {self.root}')
        return cwd

    @property
    def subdir(self):
        """Get subdirectory relative to root."""
        return self.cwd.relative_to(self.root)

    @validator('root')
    def resolve_root(cls, v):
        return v.resolve()

    @property
    def runs_yaml(self):
        """Location of runs.yaml."""
        return self.cwd / 'runs.yaml'

    @property
    def runs(self) -> List[Run]:
        """Get a list of the runs currently created from this config."""
        runs_yaml = self.runs_yaml

        if not runs_yaml.exists():
            raise IOError(
                f'Cannot find {runs_yaml}, therefore cannot show the status')

        return Runs.parse_file(runs_yaml)
