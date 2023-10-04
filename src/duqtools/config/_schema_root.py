from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from pydantic import Field, PrivateAttr

from duqtools.schema import BaseModel
from duqtools.systems.ets import Ets6SystemModel
from duqtools.systems.jetto import JettoSystemModel
from duqtools.systems.no_system import NoSystemModel

from ._schema_create import CreateConfigModel
from ._variables import VariableConfigModel


class ConfigModel(BaseModel):
    """The options for the CLI are defined by this model."""
    tag: str = Field(
        '',
        description=
        'Create a tag for the runs to identify them in slurm or `data.csv`')

    create: Optional[CreateConfigModel] = Field(
        None,
        description=
        'Configuration for the create subcommand. See model for more info.')

    extra_variables: Optional[VariableConfigModel] = Field(
        None, description='Specify extra variables for this run.')

    system: Union[NoSystemModel, Ets6SystemModel, JettoSystemModel] = Field(
        NoSystemModel(),
        description='Options specific to the system used',
        discriminator='name')

    quiet: bool = Field(
        False,
        description=
        'If true, do not output to stdout, except for mandatory prompts.')

    _path: Union[Path, str] = PrivateAttr(None)
