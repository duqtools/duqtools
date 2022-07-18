from __future__ import annotations

import logging
import shutil

from .config import cfg

logger = logging.getLogger(__name__)


def cleanup(out, force, **kwargs):
    """Read runs.yaml and clean the current directory.

    Parameters
    ----------
    out : bool
        Remove output IDS.
    """

    if cfg.workspace.runs_yaml.exists and not force:
        if (cfg.workspace.root / 'runs.yaml.old').exists():
            raise IOError(
                'runs.yaml.old exists, use --force to overwrite anyway')

    for run in cfg.workspace.runs:
        logger.info('Removing %s', run.data_in)
        run.data_in.delete()

        if out:
            logger.info('Removing %s', run.data_out)
            run.data_out.delete()

        logger.info('Removing run dir %s', run.dirname.resolve())
        shutil.rmtree(run.dirname)

    logger.info('Moving %s', cfg.workspace.runs_yaml)
    shutil.move(cfg.workspace.runs_yaml, cfg.workspace.root / 'runs.yaml.old')
