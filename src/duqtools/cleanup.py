from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from .config import Config
from .ids import ImasHandle
from .models import Locations
from .operations import op_queue

if TYPE_CHECKING:
    from .models import Run

logger = logging.getLogger(__name__)


def remove_files(*filenames: str):
    for filename in filenames:
        try:
            os.unlink(filename)
        except FileNotFoundError:
            pass


def remove_run(model: Run):
    """Remove run directory if it exists."""
    if Path(model.dirname).exists():
        op_queue.add(
            action=shutil.rmtree,
            args=(model.dirname, ),
            description='Removing run dir',
            extra_description=f'{model.dirname}',
        )


def cleanup(*, cfg: Config, out: bool, force: bool, **kwargs):
    """Read runs.yaml and clean the current directory.

    Parameters
    ----------
    cfg : Config
        Duqtools config.
    out : bool
        Remove output IDS.
    force : bool
        Force overwriting of old files.
    """
    locations = Locations(cfg=cfg)

    try:
        runs = locations.runs
    except OSError:
        runs = []
    else:
        if locations.runs_yaml.exists() and not force:
            if locations.runs_yaml_old.exists():
                raise OSError(
                    '`runs.yaml.old` exists, use --force to overwrite anyway')

    for run in runs:
        data_in = ImasHandle.model_validate(run.data_in, from_attributes=True)
        data_out = ImasHandle.model_validate(run.data_out,
                                             from_attributes=True)

        data_in.delete()

        if out:
            data_out.delete()
        else:
            op_queue.add_no_op(description='NOT Removing',
                               extra_description=f'{data_out}')

        remove_run(run)

    op_queue.add(
        action=shutil.move,
        args=(locations.runs_yaml, locations.runs_yaml_old),
        description='Moving runs.yaml',
        extra_description=f'{locations.runs_yaml_old}',
    )

    op_queue.add(
        action=remove_files,
        args=(
            'duqtools_slurm_array.err',
            'duqtools_slurm_array.out',
            'duqtools_slurm_array.sh',
        ),
        description='Removing other files',
    )
