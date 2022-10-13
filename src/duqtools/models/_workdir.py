from pathlib import Path
from typing import List

import yaml
from pydantic import validator

from ..schema.runs import Run, Runs
from ..schema.workdir import WorkDirectoryModel


class WorkDirectory(WorkDirectoryModel):

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
    def runs_yaml_old(self):
        """Location of runs.yaml.old."""
        return self.cwd / 'runs.yaml.old'

    @property
    def runs(self) -> List[Run]:
        """Get a list of the runs currently created from this config."""
        runs_yaml = self.runs_yaml

        if not runs_yaml.exists():
            raise IOError(f'Cannot find {runs_yaml}.')

        return Runs.parse_file(runs_yaml)

    @property
    def construct_runs(self) -> List[Run]:
        """Get list, but don't validate its validity."""
        runs_yaml = self.runs_yaml

        if not runs_yaml.exists():
            raise IOError(f'Cannot find {runs_yaml}.')

        with open(runs_yaml, 'r') as f:
            runs = yaml.load(f, Loader=yaml.Loader)

        return Runs.construct(runs)
