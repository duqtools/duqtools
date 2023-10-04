from __future__ import annotations

from pydantic import Field

from duqtools.utils import formatter as f

from ..schema import BaseModel


class SubmitConfigModel(BaseModel):
    """Options that can be set for each different system to change the way of
    submitting it to systems.

    These options can be set under the `system` key
    """

    submit_script_name: str = Field(
        '.llcmd', description='Script for each run that needs to be submitted')
    submit_command: str = Field('sbatch',
                                description='Submission command for slurm.')


class StatusConfigModel(BaseModel):

    in_file: str = Field('jetto.in',
                         description=f("""
            Name of the modelling input file, will be used to check
            if the subprocess has started.
            """))

    out_file: str = Field('jetto.out',
                          description=f("""
            Name of the modelling output file, will be used to
            check if the software is running.
            """))

    status_file: str = Field('jetto.status',
                             description='Name of the status file.')

    msg_completed: str = Field('Status : Completed successfully',
                               description=f("""
            Parse `status_file` for this message to check for
            completion.
            """))

    msg_failed: str = Field('Status : Failed',
                            description=f("""
            Parse `status_file` for this message to check for
            failures.
            """))

    msg_running: str = Field('Status : Running',
                             description=f("""
            Parse `status_file` for this message to check for
            running status.
            """))


class SystemModel(StatusConfigModel, SubmitConfigModel):
    pass
