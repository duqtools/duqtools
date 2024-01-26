from __future__ import annotations

import logging
import os
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, List

from ..operations import add_to_op_queue
from ._schema import ImasBaseModel

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

IMAS_PATTERN = re.compile(
    r'^((?P<user>[\\\/\w]*)\/)?(?P<db>\w+)\/(?P<shot>\d+)\/(?P<run>\d+)$')

_IMASDB = ('{db}', '3', '{shot}', '{run}')
GLOBAL_PATH_TEMPLATE = str(Path.home().parent.joinpath('{user}', 'public',
                                                       'imasdb', *_IMASDB))
LOCAL_PATH_TEMPLATE = str(Path('{user}', *_IMASDB))
PUBLIC_PATH_TEMPLATE = str(Path('shared', 'imasdb', *_IMASDB))


class ImasHandle(ImasBaseModel):

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
        path = self.path()
        assert path.exists()
        return [fn for fn in path.glob('*.h5')]

    def imasdb_path(self) -> Path:
        """Return path to imasdb."""
        return self.path().parents[3]

    @property
    def is_local_db(self):
        """Return True if the handle points to a local imas database."""
        return self.user.startswith('/')

    def exists(self) -> bool:
        """Return true if the directory exists.

        Returns
        -------
        bool
        """
        return self.path().exists()

    @add_to_op_queue('Copy imas data',
                     'from {self} to {destination}',
                     quiet=False)
    def copy_data_to(self, destination: ImasHandle):
        """Copy ids entry to given destination.

        Parameters
        ----------
        destination : ImasHandle
            Copy data to a new location.
        """
        logger.debug('Copy %s to %s', self, destination)

        destination.path().mkdir(parents=True, exist_ok=True)

        paths = list(self.paths())
        assert paths

        for src_file in paths:
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

    def get(self, *args, **kwargs):
        raise NotImplementedError

    def get_variables(self, *args, **kwargs):
        raise NotImplementedError

    def get_all_variables(self, *args, **kwargs):
        raise NotImplementedError

    def update_from(self, *args, **kwargs):
        raise NotImplementedError
