from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import yaml
from pydantic import DirectoryPath

from duqtools.ids import IDSOperation, ImasLocation

from .basemodel import BaseModel
from .config import cfg


class Run(BaseModel):
    dirname: DirectoryPath
    data: 'ImasLocation'
    operations: 'List[IDSOperation]'


class Runs(BaseModel):
    __root__: List[Run] = []


logger = logging.getLogger(__name__)


def cleanup(force: bool = False, **kwargs):
    """Read runs.yaml and clean the current directory.

    Parameters
    ----------
    force : bool
        Overwrite config if it already exists.
    kwargs :
        Unused.
    """
    # runs_yaml

    print('hello world')

    breakpoint()

    with open('runs.yaml') as f:
        d = yaml.safe_load(f)

    runs = Runs.parse_obj(d)

    # read runs.yaml
