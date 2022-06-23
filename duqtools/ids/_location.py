from __future__ import annotations

import logging
from contextlib import contextmanager
from getpass import getuser
from pathlib import Path
from typing import TYPE_CHECKING

import imas
from imas import imasdef

from duqtools.config.basemodel import BaseModel

from ._mapping import IDSMapping

if TYPE_CHECKING:
    from duqtools.jetto import JettoSettings

logger = logging.getLogger(__name__)

PATH_TEMPLATE = ('/afs/eufus.eu/user/g/{user}/public/imasdb/{db}'
                 '/3/0/ids_{shot}{run:04d}{suffix}')
SUFFIXES = (
    '.datafile',
    '.characteristics',
    '.tree',
)


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
                                 run=self.run,
                                 suffix=SUFFIXES[0]))

    def exists(self) -> bool:
        """Return true if the directory exists.

        Returns
        -------
        bool
        """
        path = self.path()
        return all(path.with_suffix(sf).exists() for sf in SUFFIXES)

    def copy_ids_entry_to(self, destination: ImasLocation):
        """Copy ids entry to given destination.

        Parameters
        ----------
        destination : ImasLocation
            Copy data to a new location.
        """
        from ._copy import copy_ids_entry
        copy_ids_entry(self, destination)

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
        """Get data from IDS entry.

        Parameters
        ----------
        key : str, optional
            Name of profiles to open.

        Returns
        -------
        data
        """
        with self.open() as data_entry:
            data = data_entry.get(key)

        return data

    def get_ids_tree(self, key: str = 'core_profiles') -> IDSMapping:
        """get the data as a simple ids (all values in memory, in a dict).

        Parameters
        ----------
        key : str, optional
            Name of profiles to open

        Returns
        -------
        IDSMapping
        """
        return IDSMapping(self.get(key))

    def entry(self, backend=imasdef.MDSPLUS_BACKEND):
        """Return reference to `imas.DBEntry.`

        Parameters
        ----------
        backend : optional
            Which IMAS backend to use

        Returns
        ------
        entry : imas.DBEntry
            IMAS database entry
        """
        return imas.DBEntry(backend, self.db, self.shot, self.run, self.user)

    @contextmanager
    def open(self, backend=imasdef.MDSPLUS_BACKEND):
        """Context manager to open database entry.

        Parameters
        ----------
        backend : optional
            Which IMAS backend to use

        Yields
        ------
        entry : imas.DBEntry
            Opened IMAS database entry
        """
        entry = self.entry(backend=backend)
        opcode, _ = entry.open()

        if opcode < 0:
            cpcode, _ = entry.create()
            if cpcode == 0:
                logger.debug('Data entry created: %s', self.path())
            else:
                raise IOError(
                    f'Cannot create data entry: {self.path()}. '
                    f'Create a new db first using `imasdb {self.db}`')
        elif opcode == 0:
            logger.debug('Data entry opened: %s', self.path())

        try:
            yield entry
        finally:
            entry.close()

    @classmethod
    def from_jset_input(cls, jset: JettoSettings) -> ImasLocation:
        """Get IMAS input location from jetto settings.

        Parameters
        ----------
        jset : JettoSettings
            Jetto settings.

        Returns
        -------
        destination : ImasLocation
            Returns the destination.
        """
        return cls(
            db=jset.machine_in,  # type: ignore
            user=jset.user_in,  # type: ignore
            run=jset.run_in,  # type: ignore
            shot=jset.shot_in)  # type: ignore

    @classmethod
    def from_jset_output(cls, jset: JettoSettings) -> ImasLocation:
        """Get IMAS output location from jetto settings.

        Parameters
        ----------
        jset : JettoSettings
            Jetto settings.

        Returns
        -------
        destination : ImasLocation
            Returns the destination.
        """
        return cls(
            db=jset.machine_out,  # type: ignore
            run=jset.run_out,  # type: ignore
            shot=jset.shot_out)  # type: ignore
