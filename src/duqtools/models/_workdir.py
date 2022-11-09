from os import getenv
from pathlib import Path
from typing import List

from ..config import cfg
from ..schema import BaseModel
from ..schema.runs import Run, Runs


class WorkDirectory(BaseModel):

    @property
    def runs_yaml(self):
        """Location of runs.yaml."""
        return Path.cwd() / 'runs.yaml'

    @property
    def runs_yaml_old(self):
        """Location of runs.yaml.old."""
        return Path.cwd() / 'runs.yaml.old'

    @property
    def runs(self) -> List[Run]:
        """Get a list of the runs currently created from this config."""
        runs_yaml = self.runs_yaml

        if not runs_yaml.exists():
            raise OSError(f'Cannot find {runs_yaml}.')

        return Runs.parse_file(runs_yaml)

    @staticmethod
    def jruns_path() -> Path:
        create = cfg.create
        if not create:
            raise OSError('create key not present in duqtools.yaml')

        if create.jruns:
            path: Path = create.jruns
        else:
            jruns = getenv('JRUNS')
            if jruns:
                path = Path(jruns)
            else:
                path = Path('./')
        return path
