from __future__ import annotations

from logging import debug
from typing import List, Optional

import yaml
from pydantic import BaseModel, DirectoryPath
from typing_extensions import Literal


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
    source: Literal['jetto.in', 'jetto.jset', 'ids']
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


class ImasLocation(BaseModel):
    db: str
    run: int
    shot: int
    user: str


class DataLocation(BaseModel):
    db: str
    run_in_start_at: int
    run_out_start_at: int


class ConfigCreate(BaseModel):
    matrix: List[IDSOperation] = []
    template: ImasLocation
    data: DataLocation


class Config(BaseModel):
    """Config class containing all configs, is a singleton and can be used with
    import duqtools.config.Config as Cfg Cfg().<variable you want>"""

    _instance = None

    # pydantic members
    submit: Submit_config = Submit_config()
    create: Optional[ConfigCreate]
    status: Status_config = Status_config()
    workspace: DirectoryPath = './workspace'

    def __init__(self, filename=None):
        """Initialize with optional filename argument."""
        if filename:
            with open(filename, 'r') as f:
                datamap = yaml.safe_load(f)
                debug(datamap)
                BaseModel.__init__(self, **datamap)

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Config._instance:
            Config._instance = object.__new__(cls)
        return Config._instance
