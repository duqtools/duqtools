from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from pydantic_yaml import parse_yaml_raw_as

from ._run import Runs

if TYPE_CHECKING:
    from ..config import Config
    from ._run import Run


class Locations:
    """Class that knows about locations within a duqtools config directory.

    Defaults to local working directory, but can be initialized with a
    known config directory.
    """

    def __init__(self,
                 *,
                 parent_dir: Optional[Path] = None,
                 cfg: Optional[Config] = None):
        if not parent_dir:
            parent_dir = Path.cwd()

        self.parent_dir = parent_dir
        self.cfg = cfg

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

        with open(runs_yaml) as f:
            model = parse_yaml_raw_as(Runs, f)

        return model.root
