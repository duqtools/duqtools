"""Functions to interface with `jetto.jset` files."""

from typing import Dict, List, TextIO, Tuple

from .._types import PathLike

HEADER = """!================================================================
!                      JETTO SETTINGS FILE
!================================================================"""

JINTRAC_CONFIG_VARS = (
    {
        'name': 'shot_in',
        'var_type': int,
        'var_name': 'SetUpPanel.idsIMASDBShot',
        'doc': 'Input IDS shot'
    },
    {
        'name': 'shot_out',
        'var_type': int,
        'var_name': 'SetUpPanel.shotNum',
        'doc': 'Output IDS shot'
    },
    {
        'name': 'run_in',
        'var_type': int,
        'var_name': 'SetUpPanel.idsIMASDBRunid',
        'doc': 'Input IDS run'
    },
    {
        'name': 'run_out',
        'var_type': int,
        'var_name': 'JobProcessingPanel.idsRunid',
        'doc': 'Output IDS run'
    },
    {
        'name': 'user_in',
        'var_type': str,
        'var_name': 'SetUpPanel.idsIMASDBUser',
        'doc': 'Input IDS user'
    },
    {
        'name': 'machine_in',
        'var_type': str,
        'var_name': 'SetUpPanel.idsIMASDBMachine',
        'doc': 'Input IDS machine'
    },
    {
        'name': 'machine_out',
        'var_type': str,
        'var_name': 'SetUpPanel.machine',
        'doc': 'Output IDS machine'
    },
    {
        'name': 'noprocessors',
        'var_type': str,
        'var_name': 'JobProcessingPanel.numProcessors',
        'doc': 'JobProcessingPanel.numProcessors'
    },
    {
        'name': 'tstart',
        'var_type': float,
        'var_name': 'SetUpPanel.startTime',
        'doc': 'Start time'
    },
    {
        'name': 'tend',
        'var_type': float,
        'var_name': 'SetUpPanel.endTime',
        'doc': 'End time'
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


class JettoSettings():

    def __init__(self, mapping: Dict[str, Dict[str, str]]):
        self.raw_mapping = mapping

    @property
    def metadata(self):
        return self.raw_mapping['File Details']

    @property
    def settings(self):
        return self.raw_mapping['Settings']

    def __new__(cls, *args, **kwargs):

        def setter(name: str, var_type):

            def f(self, value):
                self.settings[var_name] = str(value)

            return f

        def getter(name: str, var_type):

            def f(self):
                return var_type(self.settings[var_name])

            return f

        for variable in JINTRAC_CONFIG_VARS:
            var_name = variable['var_name']
            var_type = variable['var_type']
            name = variable['name']
            doc = variable['doc']
            prop = property(
                fget=getter(var_name, var_type),
                fset=setter(var_name, var_type),
                doc=doc,
            )
            setattr(cls, name, prop)

        return super().__new__(cls)

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
