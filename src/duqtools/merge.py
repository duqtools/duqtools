from __future__ import annotations

import logging
from pathlib import Path

import click

from .config import cfg
# from .ids import merge
from .ids import ImasHandle, get_ids_dataframe
from .models import WorkDirectory
from .schema.runs import Runs
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def merge(**kwargs):
    """Merge data."""

    workspace = WorkDirectory.parse_obj(cfg.workspace)

    template = ImasHandle.parse_obj(cfg.merge.template)
    target = ImasHandle.parse_obj(cfg.merge.output)

    debug('Merge input: %s', template)
    debug('Merge output: %s', target)

    handles = read_imas_handles_from_file(cfg.workspace.runs)

    for run in workspace.runs:
        data_out = ImasHandle.parse_obj(run.data_out)
