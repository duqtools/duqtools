from pydantic import Field

from .basemodel import BaseModel


class SubmitConfig(BaseModel):
    """Submit_config.

    Config class for submitting jobs
    """

    submit_script_name: str = Field(
        '.llcmd', description='Name of the submission script.')
    submit_command: str = Field('sbatch', description='Submission command.')
