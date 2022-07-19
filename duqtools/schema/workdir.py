from getpass import getuser

from pydantic import DirectoryPath, Field

from ._basemodel import BaseModel


class WorkDirectoryModel(BaseModel):
    """The workspace defines the the root directory where all simulations are
    run. This is necessary, because some programs work with relative
    directories from some root directory.

    In this way, duqtools can ensure that the current work directory is
    a subdirectory of the given root directory. All subdirectories are
    calculated as relative to the root directory.

    For example, for `rjettov`, the root directory is set to
    `/pfs/work/$USER/jetto/runs/`. Any UQ runs must therefore be
    a subdirectory.
    """

    root: DirectoryPath = Field(
        f'/pfs/work/{getuser()}/jetto/runs/',
        description='The directory from which experiments have to be run.')
