from __future__ import annotations

import logging
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

    Parsed from a string like: `imas_3_34_0_ual_4_9_3`
    """
    vsplit = imas.names[0].split('_')

    imas_version = version.parse('.'.join(vsplit[1:4]))
    ual_version = version.parse('.'.join(vsplit[5:8]))

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

    imas_version, _ = get_imas_ual_version()

    idss_in = imas.ids(source.shot, source.run)
    op = idss_in.open_env(source.user, source.db, str(imas_version.major))

    ids_not_found = op[0] < 0
    if ids_not_found:
        raise KeyError('The entry you are trying to copy does not exist')

    idss_out = imas.ids(target.shot, target.run)

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

    add_provenance_info(handle=target)
