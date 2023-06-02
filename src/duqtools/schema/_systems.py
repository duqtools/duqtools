from typing import Literal

from pydantic import Field

from ._basemodel import BaseModel
from ._description_helpers import formatter as f


class SystemModel(BaseModel):

    submit_script_name: str = '.llcmd'
    submit_command: str = Field('sbatch',
                                description='Submission command for slurm.')

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


class Ets6SystemModel(SystemModel):
    name: Literal['ets6'] = Field(
        'ets6', description='Backend system to use. Set by ConfigModel.')

    submit_script_name: str = 'run.sh'

    kepler_module: str = Field(
        description='module name used in kepler load <module>')
    kepler_load: str = Field(
        description='module name used in kepler load <module>')
    ets_xml: str = Field(
        '$ITMWORK/ETS6.xml',
        description='ETS6.XML file to use, can include for example `$ITMWORK`')


class DummySystemModel(SystemModel):
    name: Literal['dummy'] = 'dummy'
    submit_script_name: str = 'true'
    submit_command: str = 'true'


class JettoSystemModel(SystemModel):
    """The options of the JettoSystemModel, found under the `system:` key in
    the config."""
    name: Literal['jetto', 'jetto-v210921', 'jetto-v220922'] = 'jetto'

    submit_system: Literal['prominence', 'slurm', 'docker'] = Field(
        'slurm',
        description='System to submit jobs to '
        '[slurm (default), prominence, docker]')
    docker_image: str = Field('jintrac-imas',
                              description='Docker image used for submission')

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
