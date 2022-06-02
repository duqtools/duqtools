"""Functions to interface with `jetto.jset` files."""

from typing import Dict, List, TextIO, Tuple

from ..types import PathLike

HEADER = """!================================================================
!                      JETTO SETTINGS FILE
!================================================================"""


def parse_section(section: List[str]) -> Tuple[str, Dict[str, str]]:
    """Parse section of settings file.

    Parameters
    ----------
    section : List[str]
        Section in the jetto settings file

    Returns
    -------
    Tuple[str, Dict[str, str]]
        Title and dictionary with settings
    """
    title, *section = section
    title = title.strip('*')

    data = {}
    for line in section:
        key, value = line.split(':', 1)
        data[key.strip()] = value.strip()

    return title, data


def parse_jset(file: TextIO) -> Dict[str, Dict[str, str]]:
    """Parse jetto settings file.

    Parameters
    ----------
    file : TextIO
        Open file or text buffer

    Returns
    -------
    sections : Dict[str, Dict[str, str]]
        Return nested dictionary with settings from jset file.
    """
    sections = []

    read_block = False
    block: List[str] = []

    for line in file:
        line = line.strip()

        if not line:
            continue
        elif line == '*':
            read_block = True
            if block:
                sections.append(parse_section(block))
            block = []
        elif line.lower() == '*eof':
            break
        elif read_block:
            block.append(line)

    return dict(sections)


def read_jset(path: PathLike) -> Dict[str, Dict[str, str]]:
    """Read a jetto settings file saved by JAMS.

    Parameters
    ----------
    path : PathLike
        Path to jset file.

    Returns
    -------
    Dict[str, Dict[str, str]]
        Return nested dictionary with settings from jset file.
    """
    with open(path) as f:
        settings = parse_jset(f)

    return settings


def write_jset(path: PathLike, data: Dict[str, Dict[str, str]]):
    """Write a jetto settings file.

    Parameters
    ----------
    path : PathLike
        Path to which the data are saved.
    data : Dict[str, Dict[str, str]]
        Jetto settings dictionary.
    """
    pass
