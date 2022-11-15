from os import getenv
from pathlib import Path
from typing import List

from ..config import cfg
from ..schema.runs import Run, Runs


class Locations():

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

    @property
    def jruns_path(self) -> Path:
        """return the Path specified in the create->jruns config variable, or,
        if that is empty, the `$JRUNS` environment variable, or, if `$JRUNS` does not
        exists, return the current directory `./`.

        Returns
        -------
        Path
        """

        if cfg.create.jruns:  # type: ignore
            return cfg.create.jruns  # type: ignore
        elif getenv('JRUNS'):
            return Path(getenv('JRUNS'))  # type: ignore
        else:
            return Path()
