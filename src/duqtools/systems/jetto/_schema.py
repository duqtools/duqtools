from __future__ import annotations

from typing import Literal, Optional

from pydantic import DirectoryPath, Field

from duqtools.utils import formatter as f

from ..models import SystemModel


class JettoSystemModel(SystemModel):
    """The options of the JettoSystemModel, found under the `system:` key in
    the config."""
    name: Literal['jetto', 'jetto-v220922'] = 'jetto'

    submit_system: Literal['prominence', 'slurm', 'docker'] = Field(
        'slurm',
        description='System to submit jobs to '
        '[slurm (default), prominence, docker]')
    docker_image: str = Field('jintrac-imas',
                              description='Docker image used for submission')

    prominence_image: str = Field(
        'CCFE/JINTRAC/ci:latest-imas.sif',
        description='prominence image used for submission')

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

    jruns: Optional[DirectoryPath] = Field(
        None,
        description=f(
            """`jruns` defines the the root directory where all simulations are
        run for the jetto system. Because the jetto system works with relative
        directories from some root directory.

        This variable is optional. If this variable is not specified,
        duqtools will look for the `$JRUNS` environment variable,
        and set it to that. If that fails, `jruns` is set to the current directory `./`

        In this way, duqtools can ensure that the current work directory is
        a subdirectory of the given root directory. All subdirectories are
        calculated as relative to the root directory.

        For example, for `rjettov`, the root directory must be set to
        `/pfs/work/$USER/jetto/runs/`. Any UQ runs must therefore be
        a subdirectory.

        """))
