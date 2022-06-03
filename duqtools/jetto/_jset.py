"""Functions to interface with `jetto.jset` files."""

from typing import Dict, List, TextIO, Tuple

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


class JettoSettings():

    def __init__(self, mapping: Dict[str, Dict[str, str]]):
        self.raw_mapping = mapping

    @property
    def metadata(self):
        return self.raw_mapping['File Details']

    @property
    def settings(self):
        return self.raw_mapping['Settings']

    @property
    def components(self):
        components = ['JETTO']
        if self.settings['JobProcessingPanel.selIdsRunid']:
            components.append('IDSOUT')
        if self.settings['ExternalWFPanel.select']:
            components.append('HCD')
        if self.settings['SetUpPanel.selReadIds']:
            components.append('IDSIN')
        return components

    @property
    def shot_in(self):
        return int(self.settings['SetUpPanel.idsIMASDBShot'])

    @shot_in.setter
    def shot_in(self, value: int):
        self.settings['SetUpPanel.idsIMASDBShot'] = str(value)

    @property
    def shot_out(self):
        return int(self.settings['SetUpPanel.shotNum'])

    @shot_out.setter
    def shot_out(self, value: int):
        self.settings['SetUpPanel.shotNum'] = str(value)

    @property
    def run_in(self):
        return int(self.settings['SetUpPanel.idsIMASDBRunid'])

    @run_in.setter
    def run_in(self, value: int):
        self.settings['SetUpPanel.idsIMASDBRunid'] = str(value)

    @property
    def run_out(self):
        return int(self.settings['JobProcessingPanel.idsRunid'])

    @run_out.setter
    def run_out(self, value: int):
        self.settings['JobProcessingPanel.idsRunid'] = str(value)

    @property
    def user_in(self):
        return self.settings['SetUpPanel.idsIMASDBUser']

    @user_in.setter
    def user_in(self, value: str):
        self.settings['SetUpPanel.idsIMASDBUser'] = value

    @property
    def machine_in(self):
        return self.settings['SetUpPanel.idsIMASDBMachine']

    @machine_in.setter
    def machine_in(self, value: str):
        self.settings['SetUpPanel.idsIMASDBMachine'] = value

    @property
    def machine_out(self):
        return self.settings['SetUpPanel.machine']

    @machine_out.setter
    def machine_out(self, value: str):
        self.settings['SetUpPanel.machine'] = value

    @property
    def noprocessors(self):
        return int(self.settings['JobProcessingPanel.numProcessors'])

    @noprocessors.setter
    def noprocessors(self, value: str):
        self.settings['JobProcessingPanel.numProcessors'] = str(value)

    @property
    def tstart(self):
        return float(self.settings['SetUpPanel.startTime'])

    @tstart.setter
    def tstart(self, value: float):
        self.settings['SetUpPanel.startTime'] = str(value)

    @property
    def tend(self):
        return float(self.settings['SetUpPanel.endTime'])

    @tend.setter
    def tend(self, value: float):
        self.settings['SetUpPanel.endTime'] = str(value)
