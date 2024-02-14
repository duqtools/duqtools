from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, List

from ..operations import add_to_op_queue
from .__handle import _ImasHandle
from ._copy import copy_ids_entry
from ._imas import imas, imasdef

if TYPE_CHECKING:

    pass

logger = logging.getLogger(__name__)

_FILENAME = 'ids_{shot}{run:04d}{suffix}'
_IMASDB = ('{db}', '3', '0')
GLOBAL_PATH_TEMPLATE = str(Path.home().parent.joinpath('{user}', 'public',
                                                       'imasdb', *_IMASDB,
                                                       _FILENAME))
LOCAL_PATH_TEMPLATE = str(Path('{user}', *_IMASDB, _FILENAME))
PUBLIC_PATH_TEMPLATE = str(Path('shared', 'imasdb', *_IMASDB, _FILENAME))

SUFFIXES = (
    '.datafile',
    '.characteristics',
    '.tree',
)


class MdsplusImasHandle(_ImasHandle):

    def path(self, suffix=SUFFIXES[0]) -> Path:
        """Return location as Path."""
        imas_home = os.environ.get('IMAS_HOME')

        if self.is_local_db:
            template = LOCAL_PATH_TEMPLATE
        elif imas_home and self.user == 'public':
            template = imas_home + '/' + PUBLIC_PATH_TEMPLATE
        else:
            template = GLOBAL_PATH_TEMPLATE

        return Path(
            template.format(user=self.user,
                            db=self.db,
                            shot=self.shot,
                            run=self.run,
                            suffix=suffix))

    def paths(self) -> List[Path]:
        """Return location of all files as a list of Paths."""
        return [self.path(suffix) for suffix in SUFFIXES]

    def imasdb_path(self) -> Path:
        """Return path to imasdb."""
        return self.path().parents[2]

    def exists(self) -> bool:
        """Return true if the directory exists.

        Returns
        -------
        bool
        """
        path = self.path()
        return all(path.with_suffix(sf).exists() for sf in SUFFIXES)

    def copy_data_to(self, destination: _ImasHandle):
        """Copy ids entry to given destination.

        Parameters
        ----------
        destination : ImasHandle
            Copy data to a new location.
        """
        logger.debug('Copy %s to %s', self, destination)

        try:
            copy_ids_entry(self, destination)
        except Exception as err:
            raise OSError(f'Failed to copy {self}') from err

    @add_to_op_queue('Removing ids', '{self}')
    def delete(self):
        """Remove data from entry."""
        # ERASE_PULSE operation is yet supported by IMAS as of June 2022
        path = self.path()
        for suffix in SUFFIXES:
            to_delete = path.with_suffix(suffix)
            logger.debug('Removing %s', to_delete)
            try:
                to_delete.unlink()
            except FileNotFoundError:
                logger.warning('%s does not exist', to_delete)

    def entry(self, backend=imasdef.MDSPLUS_BACKEND):
        """Return reference to `imas.DBEntry.`

        Parameters
        ----------
        backend : optional
            Which IMAS backend to use

        Returns
        ------
        entry : `imas.DBEntry`
            IMAS database entry
        """
        return imas.DBEntry(backend, self.db, self.shot, self.run, self.user)
