from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, List

from ..operations import add_to_op_queue
from .__handle import _ImasHandle
from ._imas import imas, imasdef

if TYPE_CHECKING:

    pass

logger = logging.getLogger(__name__)

_IMASDB = ('{db}', '3', '{shot}', '{run}')
GLOBAL_PATH_TEMPLATE = str(Path.home().parent.joinpath('{user}', 'public',
                                                       'imasdb', *_IMASDB))
LOCAL_PATH_TEMPLATE = str(Path('{user}', *_IMASDB))
PUBLIC_PATH_TEMPLATE = str(Path('shared', 'imasdb', *_IMASDB))


class HDF5ImasHandle(_ImasHandle):

    def path(self) -> Path:
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
                            run=self.run))

    def paths(self) -> List[Path]:
        """Return location of all files as a list of Paths."""
        return [path for path in self.path().glob('*.h5')]

    def imasdb_path(self) -> Path:
        """Return path to imasdb."""
        return self.path().parents[3]

    def exists(self) -> bool:
        """Return true if the directory exists.

        Returns
        -------
        bool
        """
        return self.path().exists()

    @add_to_op_queue('Copy imas data',
                     'from {self} to {destination}',
                     quiet=True)
    def copy_data_to(self, destination: _ImasHandle):
        """Copy ids entry to given destination.

        Parameters
        ----------
        destination : ImasHandle
            Copy data to a new location.
        """
        logger.debug('Copy %s to %s', self, destination)

        destination.path().mkdir(parents=True, exist_ok=True)

        for src_file in self.paths():
            dst_file = destination.path() / src_file.name
            shutil.copyfile(src_file, dst_file)

    @add_to_op_queue('Removing ids', '{self}')
    def delete(self):
        """Remove data from entry."""
        # ERASE_PULSE operation is yet supported by IMAS as of June 2022
        for path in self.paths():
            logger.debug('Removing %s', path)
            try:
                path.unlink()
            except FileNotFoundError:
                logger.warning('%s does not exist', path)

    def entry(self):
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
        return imas.DBEntry(imasdef.HDF5_BACKEND, self.db, self.shot, self.run,
                            self.user)
