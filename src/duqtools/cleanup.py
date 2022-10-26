from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from .config import cfg
from .ids import ImasHandle
from .models import WorkDirectory
from .operations import op_queue
from .schema.runs import Run

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


def cleanup(out, force, **kwargs):
    """Read runs.yaml and clean the current directory.

    Parameters
    ----------
    out : bool
        Remove output IDS.
    """
    try:
        workspace = WorkDirectory.parse_obj(cfg.workspace)
        runs = workspace.runs
    except OSError:
        runs = ()
    else:
        if workspace.runs_yaml.exists and not force:
            if workspace.runs_yaml_old.exists():
                raise OSError(
                    '`runs.yaml.old` exists, use --force to overwrite anyway')

    for run in runs:
        data_in = ImasHandle.parse_obj(run.data_in)
        data_out = ImasHandle.parse_obj(run.data_out)

        data_in.delete()

        if out:
            data_out.delete()
        else:
            op_queue.add_no_op(description='NOT Removing',
                               extra_description=f'{data_out}')

        remove_run(run)

    op_queue.add(
        action=shutil.move,
        args=(workspace.runs_yaml, workspace.runs_yaml_old),
        description='Moving runs.yaml',
        extra_description=f'{workspace.runs_yaml_old}',
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
