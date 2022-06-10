from __future__ import annotations

import logging
from getpass import getuser
from pathlib import Path

import imas
from imas import imasdef
from pydantic import BaseModel

logger = logging.getLogger(__name__)

PATH_TEMPLATE = ('/afs/eufus.eu/user/g/{user}/public/imasdb/{db}'
                 '/3/0/ids_{shot}{run:04d}.datafile')


class ImasLocation(BaseModel):
    db: str
    run: int
    shot: int
    user: str = getuser()

    def path(self) -> Path:
        """Return location as Path."""
        return Path(
            PATH_TEMPLATE.format(user=self.user,
                                 db=self.db,
                                 shot=self.shot,
                                 run=self.run))

    def exists(self) -> bool:
        """Return true if the directory exists.

        Returns
        -------
        bool
        """
        return self.path().exists()

    def copy_ids_entry_to(self, destination: ImasLocation):
        """Copy ids entry to given destination.

        Parameters
        ----------
        destination : ImasLocation
            Copy data to a new location.
        """
        from .ids_copy import copy_ids_entry
        copy_ids_entry(self, destination)

    def copy_ids_entry_to_run(self, *, run: int) -> ImasLocation:
        """Copy ids entry to destination with given run number.

        The user is set to the current user, because we don't
        have access to write elsewhere.

        Parameters
        ----------
        run : int
            Run number of the target location.

        Returns
        -------
        destination : ImasLocation
            Returns the destination.
        """
        user = getuser()
        destination = self.copy(update={'run': run, 'user': user})
        self.copy_ids_entry_to(destination)
        return destination

    def get(self, key: str = 'core_profiles'):
        """Summary.

        Parameters
        ----------
        key : str, optional
            Name of profiles to open.

        Returns
        -------
        TYPE
            Description
        """
        data_entry = self.open()

        data = data_entry.get(key)
        data_entry.close()

        return data

    def open(self, backend=imasdef.MDSPLUS_BACKEND):
        """Open database entry."""
        entry = imas.DBEntry(backend, self.db, self.shot, self.run, self.user)
        op = entry.open()

        if op[0] < 0:
            cp = entry.create()
            if cp[0] == 0:
                logger.info('data entry created')
        elif op[0] == 0:
            logger.info('data entry opened')

        return entry
