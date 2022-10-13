from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

import click

from .config import cfg
from .ids import ImasHandle
from .models import WorkDirectory
from .operations import op_queue

logger = logging.getLogger(__name__)


def remove_files(*filenames: str):
    for filename in filenames:
        try:
            os.unlink(filename)
        except FileNotFoundError:
            pass


def cleanup(out, force, **kwargs):
    """Read runs.yaml and clean the current directory.

    Parameters
    ----------
    out : bool
        Remove output IDS.
    """
    try:
        workspace = WorkDirectory.parse_obj(cfg.workspace)
        runs = workspace.construct_runs
    except OSError:
        runs = ()
    else:
        if workspace.runs_yaml.exists and not force:
            if workspace.runs_yaml_old.exists():
                raise IOError(
                    '`runs.yaml.old` exists, use --force to overwrite anyway')

    for run in runs:
        data_in = ImasHandle.parse_obj(run.data_in)
        data_out = ImasHandle.parse_obj(run.data_out)

        data_in.delete()

        if out:
            data_out.delete()
        else:
            op_queue.add(action=lambda: None,
                         description=click.style('NOT Removing',
                                                 fg='red',
                                                 bold=True),
                         extra_description=f'{data_out}')

        if (Path(run.dirname).exists()):
            op_queue.add(
                action=shutil.rmtree,
                args=(run.dirname, ),
                description='Removing run dir',
                extra_description=f'{run.dirname}',
            )

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
