"""Functions to interface with `jetto.jset` files."""
from __future__ import annotations

from copy import deepcopy
from logging import debug
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, TextIO, Tuple

if TYPE_CHECKING:
    from .._types import PathLike

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
    settings : Dict[str, Dict[str, str]]
        Return nested dictionary with settings from jset file.
    """
    with open(path) as f:
        settings = parse_jset(f)

    return settings


def write_jset(path: PathLike, settings: Dict[str, Dict[str, str]]):
    """Write a jetto settings file.

    Parameters
    ----------
    path : PathLike
        Path to which the settings are saved.
    settings : Dict[str, Dict[str, str]]
        Jetto settings dictionary.
    """

    def _line_gen():
        yield HEADER

        for title, section in settings.items():
            yield '*'
            yield f'*{title}'
            for key, value in section.items():
                yield f'{key:<61}: {value}'

        yield from ('*', '*EOF', '')

    lines = (f'\n{line}' for line in _line_gen())

    with open(path, 'w') as f:
        f.writelines(lines)


class JettoJset:
    DEFAULT_FILENAME = 'jetto.jset'

    def __init__(self, mapping: Dict[str, Dict[str, str]]):
        self.raw_mapping = mapping

    @property
    def metadata(self):
        return self.raw_mapping['File Details']

    @property
    def settings(self):
        return self.raw_mapping['Settings']

    def get(self, field: str, section: str = None):
        if section:
            return self.settings[section][field]
        else:
            return self.settings[field]

    def set(self, field: str, value: str, section: str = None):
        if section:
            self.settings[section][field] = value
        else:
            self.settings[field] = value

    def copy(self):
        """Return a copy of this instance."""
        return deepcopy(self)

    @property
    def components(self):
        """Active components e.g. EDGE2D, JETTO, HCD (uppercase)"""
        components = ['JETTO']
        if self.settings['JobProcessingPanel.selIdsRunid']:
            components.append('IDSOUT')
        if self.settings['ExternalWFPanel.select']:
            components.append('HCD')
        if self.settings['SetUpPanel.selReadIds']:
            components.append('IDSIN')
        return components

    def to_directory(self, directory: PathLike):
        """Write a new jetto.jset to the given directory.

        Parameters
        ----------
        directory : PathLike
            Name of output directory
        """
        directory = Path(directory)

        self.settings['AppPanel.openPrvSetDir'] = str(directory)
        self.settings['JobProcessingPanel.runDirNumber'] = directory.name

        filename = directory / self.DEFAULT_FILENAME
        write_jset(filename, self.raw_mapping)
        debug('write %s', filename)

    @classmethod
    def from_file(cls, path: PathLike) -> JettoJset:
        """Read jetto settings from 'jetto.jset' file.

        Parameters
        ----------
        path : PathLike
            Path to `jetto.jset`

        Returns
        -------
        jset : JettoJset
            Instance of `JettoJset`
        """
        mapping = read_jset(path)
        jset = cls(mapping)
        return jset

    @classmethod
    def from_directory(cls, path: PathLike) -> JettoJset:
        """Read settings from 'jetto.jset' file in given directory.

        Parameters
        ----------
        path : PathLike
            Path to directory containing `jetto.jset`

        Returns
        -------
        jset : JettoJset
            Instance of `JettoJset`
        """
        filename = Path(path) / cls.DEFAULT_FILENAME
        return cls.from_file(filename)

    def copy_and_patch(self,
                       settings: dict = None,
                       metadata: dict = None) -> JettoJset:
        """Patch a copy of the jetto settings.

        Parameters
        ----------
        settings : dict, optional
            Settings to update
        metadata : dict, optional
            Metadata to update

        Returns
        -------
        jset_copy : JSet
            Patched copy.
        """
        jset_copy = self.copy()

        if settings:
            jset_copy.settings.update(settings)
        if metadata:
            jset_copy.metadata.update(metadata)

        return jset_copy
