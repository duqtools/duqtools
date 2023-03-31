from os import getenv
from pathlib import Path
from typing import Optional

from ..config import cfg
from ._run import Run, Runs


class Locations:
    """Class that knows about locations within a duqtools config directory.

    Defaults to local working directory, but can be initialized with a
    known config directory.
    """

    def __init__(self, parent_dir: Optional[Path] = None):
        if not parent_dir:
            parent_dir = Path.cwd()

        self.parent_dir = parent_dir

    @property
    def data_csv(self):
        """Location of data.csv."""
        return self.parent_dir / 'data.csv'

    @property
    def runs_yaml(self):
        """Location of runs.yaml."""
        return self.parent_dir / 'runs.yaml'

    @property
    def runs_yaml_old(self):
        """Location of runs.yaml.old."""
        return self.parent_dir / 'runs.yaml.old'

    @property
    def runs(self) -> list[Run]:
        """Get a list of the runs currently created from this config."""
        runs_yaml = self.runs_yaml

        if not runs_yaml.exists():
            raise OSError(f'Cannot find {runs_yaml}.')

        return Runs.parse_file(runs_yaml)

    @property
    def jruns_path(self) -> Path:
        """return the Path specified in the create->jruns config variable, or,
        if that is empty, the `$JRUNS` environment variable, or, if `$JRUNS`
        does not exists, return the current directory `./`.

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
