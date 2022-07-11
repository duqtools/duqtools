import logging
import shutil
import stat
from pathlib import Path

logger = logging.getLogger(__name__)


def copy_files(source_drc: Path, target_drc: Path):
    """Copy files for jetto run to destination directory.

    Parameters
    ----------
    source_drc : Path
        Source (template) directory.
    target_drc : Path
        Target directory.
    """
    for filename in (
            # '.llcmd',
            'jetto.in',
            'rjettov',
            'utils_jetto',
            'jetto.ex',
            'jetto.sin',
            'jetto.sgrid',
            'jetto.jset',
    ):
        src = source_drc / filename
        dst = target_drc / filename
        shutil.copyfile(src, dst)

    for filename in ('rjettov', 'utils_jetto'):
        path = target_drc / filename
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    logger.debug('copied files to %s', target_drc)
