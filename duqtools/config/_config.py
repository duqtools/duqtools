from __future__ import annotations

from pydantic import Field
from typing_extensions import Literal

from ._create import CreateConfig
from ._plot import PlotConfig
from ._status import StatusConfig
from ._submit import SubmitConfig
from ._workdir import WorkDirectory
from .basemodel import BaseModel


class Config(BaseModel):
    """Config class containing all configs, is a singleton and can be used with
    import duqtools.config.Config as Cfg Cfg().<variable you want>"""

    _instance = None

    plot: PlotConfig = Field(
        PlotConfig(), description='Configuration for the plotting subcommand')
    submit: SubmitConfig = Field(
        SubmitConfig(), description='Configuration for the submit subcommand')
    create: CreateConfig = Field(
        CreateConfig(), description='Configuration for the create subcommand')
    status: StatusConfig = Field(
        StatusConfig(), description='Configuration for the status subcommand')
    workspace: WorkDirectory = WorkDirectory()
    system: Literal['jetto',
                    'dummy'] = Field('jetto',
                                     description='backend system to use')
    dry_run: bool = Field(False, description='run without side effects')

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Config._instance:
            Config._instance = object.__new__(cls)
        return Config._instance


cfg = Config()
