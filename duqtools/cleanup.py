from __future__ import annotations

import logging
import shutil

from .config import cfg

logger = logging.getLogger(__name__)


def cleanup(out: bool = False, **kwargs):
    """Read runs.yaml and clean the current directory.

    Parameters
    ----------
    out : bool
        Remove output IDS.
    """

    for run in cfg.workspace.runs:
        logger.info('Removing %s', run.data_in)
        run.data_in.delete()

        if out:
            logger.info('Removing %s', run.data_out)
            run.data_out.delete()

        logger.info('Removing run dir %s', run.dirname.resolve())
        shutil.rmtree(run.dirname)

    logger.info('Removing %s', cfg.workspace.runs_yaml)
    cfg.workspace.runs_yaml.unlink()
