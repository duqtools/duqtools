from logging import debug
from typing import Optional

import yaml
from pydantic import BaseModel, DirectoryPath

from duqtools.create import ConfigCreate
from duqtools.status import Status_config
from duqtools.submit import Submit_config


class Config(BaseModel):
    """Config class containing all configs, is a singleton and can be used with
    import duqtools.config.Config as Cfg Cfg().<variable you want>"""

    _instance = None

    # pydantic members
    submit: Optional[Submit_config] = Submit_config()
    create: Optional[ConfigCreate]
    status: Optional[Status_config] = Status_config()
    workspace: DirectoryPath
    force: bool = False

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
