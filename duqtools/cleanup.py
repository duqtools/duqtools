from __future__ import annotations

import logging
import shutil

from .config import cfg

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

    for run in cfg.workspace.runs:
        logger.info('Removing %s', run.data)
        run.data.delete()

        logger.info('Removing run dir %s', run.dirname.resolve())
        shutil.rmtree(run.dirname)

    logger.info('Removing %s', cfg.workspace.runs_yaml)
    cfg.workspace.runs_yaml.unlink()
