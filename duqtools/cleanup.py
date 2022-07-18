from __future__ import annotations

import logging
import shutil

from .config import cfg
from .models.workdir import WorkDirectory

logger = logging.getLogger(__name__)


def cleanup(out: bool = False, **kwargs):
    """Read runs.yaml and clean the current directory.

    Parameters
    ----------
    out : bool
        Remove output IDS.
    """

    workspace = WorkDirectory.parse_obj(cfg.workspace)

    for run in workspace.runs:
        logger.info('Removing %s', run.data_in)
        run.data_in.delete()

        if out:
            logger.info('Removing %s', run.data_out)
            run.data_out.delete()

        logger.info('Removing run dir %s', run.dirname.resolve())
        shutil.rmtree(run.dirname)

    logger.info('Removing %s', workspace.runs_yaml)
    workspace.runs_yaml.unlink()
