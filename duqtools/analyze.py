from logging import debug, info
from os import scandir
from pathlib import Path

from duqtools.ids.ids_location import ImasLocation
from duqtools.ids.ids_simplify import SimpleCoreIDS

from .config import Config as cfg
from .status import has_status, is_completed

mockids = [{'db': 'jet', 'shot': 94875, 'run': 251}]


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

    # Gather all results and put them in a in-memory format
    # (they should be small enough so that we can analyze them)
    profiles = []
    for entry in mockids:
        # Since python 3.7 guaranteed to work
        # (dicts are always insertion-ordered)
        db, shot, run = entry.values()
        debug(db, shot, run)
        source = ImasLocation(db=db, shot=shot, run=run)

        profiles.append(source.get('core_profiles'))

    temp = SimpleCoreIDS(profiles[0])
    import pdb
    pdb.set_trace()
