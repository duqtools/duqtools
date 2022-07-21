from __future__ import annotations

import logging
import shutil

from .config import cfg
from .ids import ImasHandle
from .models import WorkDirectory

logger = logging.getLogger(__name__)


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

        logger.info('Removing %s', data_in)
        data_in.delete()

        if out:
            logger.info('Removing %s', data_out)
            data_out.delete()

        logger.info('Removing run dir %s', run.dirname.resolve())
        shutil.rmtree(run.dirname)

    logger.info('Moving %s', workspace.runs_yaml)
    shutil.move(workspace.runs_yaml, workspace.runs_yaml_old)
