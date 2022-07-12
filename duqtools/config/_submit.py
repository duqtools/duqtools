from pydantic import Field

from .basemodel import BaseModel


class SubmitConfig(BaseModel):
    """The options of the `submit` subcommand are stored under the `submit` key
    in the config.

    The config describes the commands to start the UQ runs.
    """

    submit_script_name: str = Field(
        '.llcmd', description='Name of the submission script.')
    submit_command: str = Field('sbatch', description='Submission command.')
