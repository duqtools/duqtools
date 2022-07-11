from pydantic import Field

from .basemodel import BaseModel


class StatusConfig(BaseModel):
    """Status_config."""

    status_file: str = Field('jetto.status',
                             description='Name of the status file.')
    in_file: str = Field(
        'jetto.in',
        description='Name of the modelling input file, will be used to check'
        ' if the subprocess has started.')
    out_file: str = Field(
        'jetto.out',
        description='Name of the modelling output file, will be used to check'
        ' if the subprocess is running,')

    msg_completed: str = Field(
        'Status : Completed successfully',
        description='Parse `status_file` for this message to check for'
        ' completion.')
    msg_failed: str = Field(
        'Status : Failed',
        description='Parse `status_file` for this message to check for'
        ' failures.')
    msg_running: str = Field(
        'Status : Running',
        description='Parse `status_file` for this message to check for'
        ' running status.')
