"""Functions to interface with `jetto.jset` files."""
from __future__ import annotations

from copy import deepcopy
from logging import debug
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, TextIO, Tuple

if TYPE_CHECKING:
    from .._types import PathLike
    from ..ids import ImasHandle

DEFAULT_FILENAME = 'jetto.jset'

HEADER = """!================================================================
!                      JETTO SETTINGS FILE
!================================================================"""

JINTRAC_CONFIG_VARS = (
    {
        'name': 'shot_in',
        'type': int,
        'key': 'SetUpPanel.idsIMASDBShot',
        'doc': 'Input IDS shot'
    },
    {
        'name': 'shot_out',
        'type': int,
        'key': 'SetUpPanel.shotNum',
        'doc': 'Output IDS shot'
    },
    {
        'name': 'run_in',
        'type': int,
        'key': 'SetUpPanel.idsIMASDBRunid',
        'doc': 'Input IDS run'
    },
    {
        'name': 'run_out',
        'type': int,
        'key': 'JobProcessingPanel.idsRunid',
        'doc': 'Output IDS run'
    },
    {
        'name': 'user_in',
        'type': str,
        'key': 'SetUpPanel.idsIMASDBUser',
        'doc': 'Input IDS user'
    },
    {
        'name': 'machine_in',
        'type': str,
        'key': 'SetUpPanel.idsIMASDBMachine',
        'doc': 'Input IDS machine'
    },
    {
        'name': 'machine_out',
        'type': str,
        'key': 'SetUpPanel.machine',
        'doc': 'Output IDS machine'
    },
    {
        'name': 'noprocessors',
        'type': str,
        'key': 'JobProcessingPanel.numProcessors',
        'doc': 'JobProcessingPanel.numProcessors'
    },
    {
        'name': 'tstart',
        'type': float,
        'key': 'SetUpPanel.startTime',
        'doc': 'Start time'
    },
    {
        'name': 'tend',
        'type': float,
        'key': 'SetUpPanel.endTime',
        'doc': 'End time'
    },
    {
        'name': 'run_dir',
        'type': str,
        'key': 'AppPanel.openPrvSetDir',
        'doc': 'Location of the run directory'
    },
    {
        'name': 'run_dir_name',
        'type': str,
        'key': 'JobProcessingPanel.runDirNumber',
        'doc': 'Name of the run directory'
    },
)


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


class JettoSettings:

    def __init__(self, mapping: Dict[str, Dict[str, str]]):
        self.raw_mapping = mapping

    @property
    def metadata(self):
        return self.raw_mapping['File Details']

    @property
    def settings(self):
        return self.raw_mapping['Settings']

    def __new__(cls, *args, **kwargs):

        def setter(jset_key: str, jset_type):

            def f(self, value):
                self.settings[jset_key] = str(value)

            return f

        def getter(jset_key: str, jset_type):

            def f(self):
                return jset_type(self.settings[jset_key])

            return f

        for variable in JINTRAC_CONFIG_VARS:
            jset_key = variable['key']
            jset_type = variable['type']
            name = variable['name']
            doc = variable['doc']
            prop = property(
                fget=getter(jset_key, jset_type),
                fset=setter(jset_key, jset_type),
                doc=doc,
            )
            setattr(cls, name, prop)

        return super().__new__(cls)

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

        self.run_dir = str(directory)
        self.run_dir_name = directory.name

        filename = directory / DEFAULT_FILENAME
        write_jset(filename, self.raw_mapping)
        debug('write %s', filename)

    @classmethod
    def from_file(cls, path: PathLike) -> JettoSettings:
        """Read JettoSettings from 'jetto.jset' file.

        Parameters
        ----------
        path : PathLike
            Path to `jetto.jset`

        Returns
        -------
        jset : JettoSettings
            Instance of `JettoSettings`
        """
        mapping = read_jset(path)
        jset = cls(mapping)
        return jset

    @classmethod
    def from_directory(cls, path: PathLike) -> JettoSettings:
        """Read JettoSettings from 'jetto.jset' file in given directory.

        Parameters
        ----------
        path : PathLike
            Path to directory containing `jetto.jset`

        Returns
        -------
        jset : JettoSettings
            Instance of `JettoSettings`
        """
        filename = Path(path) / DEFAULT_FILENAME
        return cls.from_file(filename)

    def copy_and_patch(self,
                       settings: dict = None,
                       metadata: dict = None) -> JettoSettings:
        """Patch a copy of the jetto settings.

        Parameters
        ----------
        settings : dict, optional
            Settings to update
        metadata : dict, optional
            Metadata to update

        Returns
        -------
        jset_copy : JettoSettings
            Patched copy.
        """
        jset_copy = self.copy()

        if settings:
            jset_copy.settings.update(settings)
        if metadata:
            jset_copy.metadata.update(metadata)

        return jset_copy

    def set_imas_locations(self, inp: ImasHandle,
                           out: ImasHandle) -> JettoSettings:
        """Make a copy with updated IDS locations for input / output.

        Parameters
        ----------
        inp : ImasHandle
            IMAS description of where the input data is stored.
        out : ImasHandle
            IMAS description of where the output data should be stored.

        Returns
        -------
        jset_new : JettoSettings
            Copy of the jetto settings with updated IDS locations.
        """
        jset_new = self.copy()

        jset_new.user_in = inp.user
        jset_new.machine_in = inp.db
        jset_new.shot_in = inp.shot
        jset_new.run_in = inp.run

        jset_new.machine_out = out.db
        jset_new.shot_out = out.shot
        jset_new.run_out = out.run

        return jset_new
