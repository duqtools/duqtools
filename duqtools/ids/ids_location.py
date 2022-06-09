from __future__ import annotations

from getpass import getuser
from pathlib import Path

from pydantic import BaseModel

PATH_TEMPLATE = ('/afs/eufus.eu/user/g/{user}/public/imasdb/{db}'
                 '/3/0/ids_{shot}{run:04d}.xyz')


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

        Parameters
        ----------
        run : int
            Run number of the target location.

        Returns
        -------
        destination : ImasLocation
            Returns the destination.
        """
        destination = self.copy(update={'run': run})
        self.copy_ids_entry_to(destination)
        return destination
