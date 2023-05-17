from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from .._logging_utils import LoggingContext
from ..operations import add_to_op_queue
from ._imas import Parser, imas

if TYPE_CHECKING:
    from .ids import ImasHandle


def get_imas_version():
    """Get imas/ual versions.

    Changed in 3.10.6, find new ways to find this info
    """

    imas_version = imas._ual_lowlevel.sys.version_info

    return imas_version


def add_provenance_info(handle: ImasHandle, ids: str = 'core_profiles'):
    """Add provenance information to handle.

    Parameters
    ----------
    handle : ImasHandle
        Handle to add provenance information to.
    ids : str, optional
        Which IDS to add provenance to.
    """

    import git
    import pkg_resources  # type: ignore

    with handle.open() as data_entry_target:
        entry = data_entry_target.get(ids)

        # Set the name
        entry.code.name = 'duqtools'

        # Get the commit if we are in a repository
        try:
            entry.code.commit = git.Repo(
                Path(__file__).parent,
                search_parent_directories=True).head.object.hexsha
        except Exception:
            entry.code.commit = 'unknown'

        # Set the version if available
        try:
            entry.code.version = pkg_resources.get_distribution(
                'duqtools').version
        except Exception:
            entry.code.version = 'unknown'

        # The repository, always set to duqtools
        entry.code.repository = 'https://github.com/duqtools/duqtools/'

        entry.put(db_entry=data_entry_target)


@add_to_op_queue('Copy ids from template to', '{target}', quiet=True)
def copy_ids_entry(source: ImasHandle, target: ImasHandle):
    """Copies the ids entry to a new location.

    Parameters
    ----------
    source : ImasHandle
        Source ids entry
    target : ImasHandle
        Target ids entry

    Raises
    ------
    KeyError
        If the IDS entry you are trying to copy does not exist.
    """
    target.validate()

    imas_version = get_imas_version()
    os.environ[
        'IMAS_VERSION'] = f'{imas_version.major}.{imas_version.minor},{imas_version.micro}'

    for src_file, dst_file in zip(source.paths(), target.paths()):
        shutil.copyfile(src_file, dst_file)

    add_provenance_info(handle=target)
