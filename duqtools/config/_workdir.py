from getpass import getuser
from pathlib import Path
from typing import List

from pydantic import DirectoryPath, Field, validator

from ._runs import Run, Runs
from .basemodel import BaseModel


class WorkDirectory(BaseModel):
    """The workspace defines the the root directory where all simulations are
    run. This is necessary, because some programs work with relative
    directories from some root directory.

    In this way, duqtools can ensure that the current work directory is
    a subdirectory of the given root directory. All subdirectories are
    calculated as relative to the root directory.

    For example, for `rjettov`, the root directory is set to
    `/pfs/work/$USER/jetto/runs/`. Any UQ runs must therefore be
    a subdirectory.
    """

    root: DirectoryPath = Field(
        f'/pfs/work/{getuser()}/jetto/runs/',
        description='The directory from which experiments have to be run.')

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
