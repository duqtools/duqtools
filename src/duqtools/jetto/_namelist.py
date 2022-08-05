"""Functions to interface with `jetto.in` namelists."""

from typing import Any, Dict, List, Tuple

import f90nml

from .._types import PathLike

HEADER_ROWS = 17


def read_namelist(
    path: PathLike,
    header_rows: int = HEADER_ROWS
) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
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
    with open(path) as f:
        header = [next(f) for _ in range(HEADER_ROWS)]
        nml = f90nml.read(f)

    return header, nml.todict()


def write_namelist(path: PathLike,
                   namelist: dict,
                   header: List[str] = None,
                   **kwargs):
    """Write dictionary fortran namelist (i.e. `jetto.in`).

    Parameters
    ----------
    path : PathLike
        Path to namelist
    namelist : dict
        Fortran namelist in dictionary format
    """
    nml = f90nml.Namelist(**namelist)

    with open(path, 'w') as f:
        if header:
            f.writelines(header)

        hline = '-' * 80 + '\n'
        title = ' Namelist : {}\n'
        blank = '\n'

        for title, fields in nml.items():
            f.writelines(
                (blank, hline, title.format(title.upper()), hline, blank))

            section = f90nml.Namelist({title: fields})

            section.end_comma = True
            section.uppercase = True
            section.indent = ' '

            section.write(f)

            f.write(blank)
