import os
from typing import TypeVar

import f90nml

try:
    import imas
except ImportError:
    pass

PathLike = TypeVar('PathLike', str, bytes, os.PathLike)


def fetch_ids_data(
    *,
    shot: int,
    run: int,
    user_name: str,
    db_name: str,
) -> 'imas.DBEntry':
    """Fetch entry from IMAS database.

    e.g.
    ```
    db = fetch_ids_data(
        shot = 94875, run = 1, user_name = 'g2aho', db_name = 'jet')
    # -> /afs/eufus.eu/user/g/g2aho/public/imasdb/jet/3/0/ids_948750001.*

    db = fetch_ids_data(
        shot=94875, run=250, user_name='g2ssmee', db_name='jet')
    # -> /afs/eufus.eu/user/g/g2ssmee/public/imasdb/jet/3/0/ids_948750250.*
    ```

    Parameters
    ----------
    shot : int
        Shot number
    run : int
        Run number
    user_name : str
        User name
    db_name : str
        Database name

    Returns
    -------
    db : imas.DBEntry
        Imas database entry
    """
    backend = imas.imasdef.MDSPLUS_BACKEND
    db = imas.DBEntry(
        backend_id=backend,
        shot=shot,
        run=run,
        user_name=user_name,
        db_name=db_name,
    )

    return db


def read_namelist(path: PathLike) -> dict:
    """Read fortran namelist (i.e. `jetto.in`).

    Parameters
    ----------
    path : PathLike
        Path to namelist

    Returns
    -------
    namelist : dict
        Returns parameters in namelist as dict
    """
    return f90nml.read(path).todict()


def write_namelist(path: PathLike, namelist: dict):
    """Write dictionary fortran namelist (i.e. `jetto.in`).

    Parameters
    ----------
    path : PathLike
        Path to namelist
    namelist : dict
        Fortran namelist in dictionary format
    """
    nml = f90nml.Namelist(**namelist)
    nml.write(path)


def patch_namelist(path: PathLike, patch: dict, out: PathLike):
    """Patch parameters in namelist.

    i.e. in the case of `jetto.in`, this preserves
    the comments in the header, which are required for
    `rjettov`.

    Parameters
    ----------
    path : str
        Path to original namelist
    patch : dict
        Dictionary with variables to patch / add
    out : PathLike
        Path to write patched `jetto.in` file.

    Returns
    -------
    patched_nml : dict
        Return patched namelist as dictionary
    """
    patched_nml = f90nml.patch(path, patch, out)
    return patched_nml.todict()
