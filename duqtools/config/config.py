from __future__ import annotations

from typing import Union

from pydantic import Field

from .basemodel import BaseModel
from .create import CreateConfig
from .plot import PlotConfig
from .status import StatusConfig
from .submit import SubmitConfig
from .system import DummySystem, JettoSystem
from .workdir import WorkDirectory


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
    system: Union[JettoSystem, DummySystem] = Field(default=JettoSystem(),
                                                    discriminator='name')

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Config._instance:
            Config._instance = object.__new__(cls)
        return Config._instance


cfg = Config()
