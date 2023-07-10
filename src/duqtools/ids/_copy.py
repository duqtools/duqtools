from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from packaging import version

from .._logging_utils import LoggingContext
from ..operations import add_to_op_queue
from ._imas import Parser, imas

if TYPE_CHECKING:
    from .ids import ImasHandle


def get_imas_ual_version():
    """Get imas/ual versions.

    Parsed from a string like:
    - `imas_3_34_0_ual_4_9_3`
    - `imas_3_38_0_dev1_ual_4_11_0`
    """
    vsplit = imas.names[0].split('_')

    ual_start = vsplit.index('ual')
    imas_start = vsplit.index('imas')

    imas_version = version.parse('.'.join(vsplit[imas_start + 1:ual_start]))
    ual_version = version.parse('.'.join(vsplit[ual_start + 1:]))

    return imas_version, ual_version


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


def copy_ids_entry_complex(source: ImasHandle, target: ImasHandle):
    """Old way of copying by reading and writing via IMAS.

    Copies the ids entry to a new location.

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
    imas_version, _ = get_imas_ual_version()

    idss_in = imas.ids(source.shot, source.run)  # type: ignore
    op = idss_in.open_env(source.user, source.db, str(imas_version.major))

    ids_not_found = op[0] < 0
    if ids_not_found:
        raise KeyError('The entry you are trying to copy does not exist')

    idss_out = imas.ids(target.shot, target.run)  # type: ignore

    idss_out.create_env(target.user, target.db, str(imas_version.major))
    idx = idss_out.expIdx

    parser = Parser.load_idsdef()

    # Temporarily hide warnings, because this loop is very spammy
    with LoggingContext(level=logging.CRITICAL):

        for ids_info in parser.idss:
            name = ids_info['name']
            maxoccur = int(ids_info['maxoccur'])

            if name in ('ec_launchers', 'numerics', 'sdn'):
                continue

            for i in range(maxoccur + 1):
                ids = idss_in.__dict__[name]
                ids.get(i)
                ids.setExpIdx(idx)  # this line sets the index to the output
                ids.put(i)

    idss_in.close()
    idss_out.close()


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

    if os.environ.get('SIMPLE_IDS_COPY'):
        for src_file, dst_file in zip(source.paths(), target.paths()):
            shutil.copyfile(src_file, dst_file)
    else:
        copy_ids_entry_complex(source, target)

    add_provenance_info(handle=target)
