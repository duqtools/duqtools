"""Functions to interface with `jetto.in` namelists."""

import f90nml

from .._types import PathLike


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
