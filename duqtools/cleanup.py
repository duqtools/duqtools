from __future__ import annotations

import logging
import shutil
from typing import List

import yaml
from pydantic import DirectoryPath

from duqtools.ids import IDSOperation, ImasLocation

from .basemodel import BaseModel
from .config import cfg

logger = logging.getLogger(__name__)


class Run(BaseModel):
    dirname: DirectoryPath
    data: 'ImasLocation'
    operations: 'List[IDSOperation]'


class Runs(BaseModel):
    __root__: List[Run] = []

    def __iter__(self):
        yield from self.__root__


def cleanup(force: bool = False, **kwargs):
    """Read runs.yaml and clean the current directory.

    Parameters
    ----------
    force : bool
        Overwrite config if it already exists.
    kwargs :
        Unused.
    """
    runs_yaml = cfg.workspace.runs_yaml

    with open(runs_yaml) as f:
        mapping = yaml.safe_load(f)
        runs = Runs.parse_obj(mapping)

    for run in runs:
        logger.info('Removing %s', run.data)
        run.data.delete()

        logger.info('Removing run dir %s', run.dirname.resolve())
        shutil.rmtree(run.dirname)

    logger.info('Removing %s', runs_yaml)
    runs_yaml.unlink()
