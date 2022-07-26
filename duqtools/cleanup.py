from __future__ import annotations

import logging
import shutil

import click

from .config import cfg
from .ids import ImasHandle
from .models import WorkDirectory
from .operations import confirm_operations, op_queue

logger = logging.getLogger(__name__)


@confirm_operations
def cleanup(out, force, **kwargs):
    """Read runs.yaml and clean the current directory.

    Parameters
    ----------
    out : bool
        Remove output IDS.
    """
    workspace = WorkDirectory.parse_obj(cfg.workspace)

    if workspace.runs_yaml.exists and not force:
        if workspace.runs_yaml_old.exists():
            raise IOError(
                '`runs.yaml.old` exists, use --force to overwrite anyway')

    for run in workspace.runs:
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

        op_queue.add(action=shutil.rmtree,
                     args=(run.dirname, ),
                     description='Removing run dir',
                     extra_description=f'{run.dirname}')

    op_queue.add(action=shutil.move,
                 args=(workspace.runs_yaml, workspace.runs_yaml_old),
                 description='Moving runs.yaml',
                 extra_description=f'{workspace.runs_yaml_old}')
