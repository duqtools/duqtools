from __future__ import annotations

import logging
from typing import List, Optional

import yaml
from pydantic import BaseModel, DirectoryPath
from typing_extensions import Literal

from duqtools.ids.ids_location import ImasLocation

logger = logging.getLogger(__name__)


class Plot(BaseModel):
    x: Optional[str]
    # TODO, make y axis time-variable by replacing "0" with "*" for example
    y: str = 'profiles_1d/0/electrons/density_thermal'

    _xlabel: str
    _ylabel: str

    add_time_slider: bool = False

    def __get_xlabel(self):
        return self._xlabel if hasattr(self, '_xlabel') else self.x

    def __set_xlabel(self, var: str):
        self._xlabel = var

    def __get_ylabel(self):
        return self._ylabel if hasattr(self, '_ylabel') else self.y

    def __set_ylabel(self, var: str):
        self._ylabel = var

    xlabel = property(__get_xlabel, __set_xlabel)
    ylabel = property(__get_ylabel, __set_ylabel)


class Plot_config(BaseModel):
    data: List[ImasLocation] = [
        ImasLocation(**{
            'db': 'jet',
            'shot': 94875,
            'run': 251,
            'user': 'g2vazizi'
        })
    ]
    plots: List[Plot] = [Plot()]


class Status_config(BaseModel):
    """Status_config."""

    msg_completed: str = 'Status : Completed successfully'
    msg_failed: str = 'Status : Failed'
    msg_running: str = 'Status : Running'


class Submit_config(BaseModel):
    """Submit_config.

    Config class for submitting jobs
    """

    submit_script_name: str = '.llcmd'
    status_file: str = 'jetto.status'


class Variable(BaseModel):
    source: Literal['jetto.in', 'jetto.jset']
    key: str
    values: list

    def expand(self):
        return tuple({
            'source': self.source,
            'key': self.key,
            'value': value
        } for value in self.values)


class IDSOperation(BaseModel):
    ids: str
    operator: Literal['add', 'multiply']
    values: List[float]

    def expand(self):
        return tuple({
            'ids': self.ids,
            'operator': self.operator,
            'value': value
        } for value in self.values)


class DataLocation(BaseModel):
    db: str
    run_in_start_at: int
    run_out_start_at: int


class ConfigCreate(BaseModel):
    matrix: List[IDSOperation] = []
    # template: ImasLocation
    template: DirectoryPath
    data: DataLocation


class Config(BaseModel):
    """Config class containing all configs, is a singleton and can be used with
    import duqtools.config.Config as Cfg Cfg().<variable you want>"""

    _instance = None

    # pydantic members
    submit: Submit_config = Submit_config()
    create: Optional[ConfigCreate]
    status: Status_config = Status_config()
    plot: Plot_config = Plot_config()
    workspace: DirectoryPath = './workspace'

    def __init__(self, filename=None):
        """Initialize with optional filename argument."""
        if filename:
            with open(filename, 'r') as f:
                datamap = yaml.safe_load(f)
                logger.debug(datamap)
                BaseModel.__init__(self, **datamap)

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Config._instance:
            Config._instance = object.__new__(cls)
        return Config._instance
