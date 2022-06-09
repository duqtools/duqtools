from logging import debug, info
from os import scandir
from pathlib import Path

from .config import Config as cfg
from .status import has_status, is_completed

mockids = [{
    'db': 'duqtools',
    'shot': 1,
    'index': 1
}, {
    'db': 'duqtools',
    'shot': 1,
    'index': 2
}, {
    'db': 'duqtools',
    'shot': 1,
    'index': 3
}]


def analyze(**kwargs):
    """analyze.

    Parameters
    ----------
    kwargs :
        kwargs
    """

    dirs = [
        Path(entry) for entry in scandir(cfg().workspace) if entry.is_dir()
    ]
    debug('Case directories: %s' % dirs)
    dirs_status = [dir for dir in dirs if has_status(dir)]
    dirs_completed = [dir for dir in dirs_status if is_completed(dir)]
    info('Total number of directories with Completed status  : %i' %
         len(dirs_completed))

    debug('Extracting imas info from completed cases')

    # TODO get IDS locations, use mockids now

    for entry in mockids:
        # data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, index)
        pass
