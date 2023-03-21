from __future__ import annotations

import logging
import os
import re
from contextlib import contextmanager
from getpass import getuser
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from pydantic import validator

from ..config import lookup_vars, var_lookup
from ..operations import add_to_op_queue
from ..schema import IDSVariableModel, ImasBaseModel
from ._copy import copy_ids_entry
from ._imas import imas, imasdef
from ._mapping import IDSMapping
from ._rebase import squash_placeholders

if TYPE_CHECKING:
    import xarray as xr

logger = logging.getLogger(__name__)

_FILENAME = 'ids_{shot}{run:04d}{suffix}'
_IMASDB = ('{db}', '3', '0')
GLOBAL_PATH_TEMPLATE = str(Path.home().parent.joinpath('{user}', 'public',
                                                       'imasdb', *_IMASDB,
                                                       _FILENAME))
LOCAL_PATH_TEMPLATE = str(Path('{user}', *_IMASDB, _FILENAME))

SUFFIXES = (
    '.datafile',
    '.characteristics',
    '.tree',
)

IMAS_PATTERN = re.compile(
    r'^((?P<user>\w+)/)?(?P<db>\w+)/(?P<shot>\d+)/(?P<run>\d+)$')


def _patch_str_repr(obj: object):
    """Reset str/repr methods to default."""
    import types

    def true_repr(x):
        type_ = type(x)
        module = type_.__module__
        qualname = type_.__qualname__
        return f'<{module}.{qualname} object at {hex(id(x))}>'

    obj.__str__ = types.MethodType(true_repr, obj)  # type: ignore
    obj.__repr__ = types.MethodType(true_repr, obj)  # type: ignore


class ImasHandle(ImasBaseModel):

    def __str__(self):
        return f'{self.user}/{self.db}/{self.shot}/{self.run}'

    @classmethod
    def from_string(cls, string: str) -> ImasHandle:
        """Return location from formatted string.

        Format:

            <user>/<db>/<shot>/<run>
            <db>/<shot>/<run>

        Default to the current user if the user is not specified.

        For example:

            g2user/jet/91234/555

        Parameters
        ----------
        string : str
            Input string containing imas db path

        Returns
        -------
        ImasHandle
        """
        match = IMAS_PATTERN.match(string)

        if match:
            return cls(**match.groupdict())

        raise ValueError(f'Could not match {string!r}')

    @validator('user')
    def user_rel_path(cls, v, values):
        # Override user if we have a relative location
        if values['relative_location']:
            logger.info(
                f'Updating imasdb location with relative location {values["relative_location"]}'
            )
            return os.path.abspath(values['relative_location'])
        return v

    def validate(self):
        """Validate the user.

        If the user is a path, then create it.

        Raises
        ------
        ValueError:
            If the user is invalid.
        """
        if self.is_local_db:
            # jintrac v220922
            self.path().parent.mkdir(parents=True, exist_ok=True)
        elif self.user == getuser() or self.user == 'public':
            # jintrac v210921
            pass
        else:
            raise ValueError(f'Invalid user: {self.user}')

    def to_string(self) -> str:
        """Generate string representation of Imas location."""
        return f'{self.user}/{self.db}/{self.shot}/{self.run}'

    @property
    def is_local_db(self):
        """Return True if the handle points to a local imas database."""
        return self.user.startswith('/')

    def path(self) -> Path:
        """Return location as Path."""
        if self.is_local_db:
            template = LOCAL_PATH_TEMPLATE
        else:
            template = GLOBAL_PATH_TEMPLATE

        return Path(
            template.format(user=self.user,
                            db=self.db,
                            shot=self.shot,
                            run=self.run,
                            suffix=SUFFIXES[0]))

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

    def copy_data_to(self, destination: ImasHandle):
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

    def get_raw_data(self, ids: str = 'core_profiles', **kwargs):
        """Get data from IDS entry.

        Parameters
        ----------
        ids : str, optional
            Name of profiles to open.
        **kwargs
            These keyword parameters are passed to `ImasHandle.open()`.

        Returns
        -------
        data
        """
        with self.open(**kwargs) as data_entry:
            data = data_entry.get(ids)

        # reset string representation because output is extremely lengthy
        _patch_str_repr(data)

        return data

    def get(self, ids: str = 'core_profiles') -> IDSMapping:
        """Map the data to a dict-like structure.

        Parameters
        ----------
        ids : str, optional
            Name of profiles to open

        Returns
        -------
        IDSMapping
        """
        raw_data = self.get_raw_data(ids)
        return IDSMapping(raw_data)

    def get_all_variables(
        self,
        extra_variables: Sequence[IDSVariableModel] = [],
        squash: bool = True,
        ids: str = 'core_profiles',
        **kwargs,
    ) -> xr.Dataset:
        """Get all variables that duqtools knows of from selected ids from the
        dataset.

        This function looks up the data location from the
        `duqtools.config.var_lookup` table

        Parameters
        ----------
        variables : Sequence[IDSVariableModel]
            Extra variables to load in addition to the ones known by duqtools.
        squash : bool
            Squash placeholder variables

        Returns
        -------
        ds : xarray
            The data in `xarray` format.
        **kwargs
            These keyword arguments are passed to `IDSMapping.to_xarray()`

        Raises
        ------
        ValueError
            When variables are from multiple IDSs.
        """
        idsvar_lookup = var_lookup.filter_ids(ids)
        variables = list(
            set(list(extra_variables) + list(idsvar_lookup.keys())))
        return self.get_variables(variables,
                                  squash,
                                  empty_var_ok=True,
                                  **kwargs)

    def get_variables(
        self,
        variables: Sequence[str | IDSVariableModel],
        squash: bool = True,
        **kwargs,
    ) -> xr.Dataset:
        """Get variables from data set.

        This function looks up the data location from the
        `duqtools.config.var_lookup` table, and returns

        Parameters
        ----------
        variables : Sequence[Union[str, IDSVariableModel]]
            Variable names of the data to load.
        squash : bool
            Squash placeholder variables

        Returns
        -------
        ds : xarray
            The data in `xarray` format.
        **kwargs
            These keyword arguments are passed to `IDSMapping.to_xarray()`

        Raises
        ------
        ValueError
            When variables are from multiple IDSs.
        """
        var_models = lookup_vars(variables)

        idss = {var.ids for var in var_models}

        if len(idss) > 1:
            raise ValueError(
                f'All variables must belong to the same IDS, got {idss}')

        ids = var_models[0].ids

        data_map = self.get(ids)

        ds = data_map.to_xarray(variables=var_models, **kwargs)

        if squash:
            ds = squash_placeholders(ds)

        return ds

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

    @contextmanager
    def open(self, backend=imasdef.MDSPLUS_BACKEND, create: bool = False):
        """Context manager to open database entry.

        Parameters
        ----------
        backend : optional
            Which IMAS backend to use
        create : bool, optional
            Create empty database entry if it does not exist.

        Yields
        ------
        entry : `imas.DBEntry`
            Opened IMAS database entry
        """
        entry = self.entry(backend=backend)
        opcode, _ = entry.open()

        if opcode == 0:
            logger.debug('Data entry opened: %s', self)
        elif create:
            cpcode, _ = entry.create()
            if cpcode == 0:
                logger.debug('Data entry created: %s', self)
            else:
                raise OSError(
                    f'Cannot create data entry: {self}. '
                    f'Create a new db first using `imasdb {self.db}`')
        else:
            raise OSError(f'Data entry does not exist: {self}')

        try:
            yield entry
        finally:
            entry.close()
