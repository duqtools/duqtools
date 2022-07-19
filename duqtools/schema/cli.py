from getpass import getuser
from typing import List, Union

from pydantic import DirectoryPath, Field, validator
from typing_extensions import Literal

from ._description_helpers import formatter as f
from .basemodel import BaseModel
from .data_location import DataLocation
from .dimensions import IDSOperationDim, IDSSamplerDim
from .matrix_samplers import (CartesianProduct, HaltonSampler, LHSSampler,
                              SobolSampler)
from .plot import PlotModel
from .work_dir import WorkDirectoryModel


class DeprecatedValueError(ValueError):
    ...


class CreateConfigModel(BaseModel):
    """The options of the `create` subcommand are stored in the `create` key in
    the config."""
    dimensions: List[Union[IDSOperationDim, IDSSamplerDim]] = Field(
        [IDSOperationDim(), IDSSamplerDim()],
        description=f("""
        The `dimensions` specifies the dimensions of the matrix to sample
        from. Each dimension is a compound set of operations to apply.
        From this, a matrix all possible combinations is generated.
        Essentially, it generates the
        [Cartesian product](en.wikipedia.org/wiki/Cartesian_product)
        of all operations. By specifying a different `sampler`, a subset of
        this hypercube can be efficiently sampled.
        """))

    matrix: List = Field([],
                         deprecated=True,
                         description='Use `dimensions` instead.')

    sampler: Union[LHSSampler, HaltonSampler, SobolSampler,
                   CartesianProduct] = Field(default=LHSSampler(),
                                             discriminator='method',
                                             description=f("""
        For efficient UQ, it may not be necessary to sample the entire matrix
        or hypercube. By default, the cartesian product is taken. For more
        efficient sampling of the space, the following `method` choices are
        available:
        [`latin-hypercube`](en.wikipedia.org/wiki/Latin_hypercube_sampling),
        [`sobol`](en.wikipedia.org/wiki/Sobol_sequence),
        [`halton`](en.wikipedia.org/wiki/Halton_sequence).
        Where `n_samples` gives the number of samples to extract.
        """))

    template: DirectoryPath = Field(
        f'/pfs/work/{getuser()}/jetto/runs/duqtools_template',
        description=f("""
        The create subroutine takes as a template directory. This can be a
        directory with a finished run, or one just stored by JAMS (but not yet
        started). Duqtools uses the input IDS machine (db) name, user, shot,
        run number from e.g. `jetto.in` to find the data to modify for the
        UQ runs.
        """))

    data: DataLocation = Field(DataLocation(),
                               description=f("""
        Where to store the in/output IDS data.
        The data key specifies the machine or imas
        `db` name where to store the data (`db`). duqtools will write the input
        data files for UQ start with the run number given by `run_in_start_at`.
        The data generated by the UQ runs (e.g. from jetto) will be stored
        starting by the run number given by `run_out_start_at`.
        """))

    @validator('matrix')
    def deprecate_matrix(v):
        raise DeprecatedValueError(
            "'matrix' has been deprecated, use 'dimensions' instead.")


class SubmitConfigModel(BaseModel):
    """The options of the `submit` subcommand are stored under the `submit` key
    in the config.

    The config describes the commands to start the UQ runs.
    """

    submit_script_name: str = Field(
        '.llcmd', description='Name of the submission script.')
    submit_command: str = Field('sbatch', description='Submission command.')


class StatusConfigModel(BaseModel):
    """The options of the `status` subcommand are stored under the `status` key
    in the config.

    These only need to be changed if the modeling software changes.
    """

    status_file: str = Field('jetto.status',
                             description='Name of the status file.')
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


class PlotConfigModel(BaseModel):
    """The options of the plot subcommand are stored under the `plot` key in
    the config.

    Plots are specified as a list under the `plots` key. Multiple plots
    can be defined, and they will be written sequentially as .png files
    to the current working directory.
    """
    plots: List[PlotModel] = [
        PlotModel(),
        PlotModel(
            x='profiles_1d/0/grid/rho_tor_norm',
            y='profiles_1d/0/t_i_average',
            xlabel='Rho tor.',
            ylabel='Ion temperature',
        )
    ]


class ConfigModel(BaseModel):
    """The options for the CLI are defined by this model."""
    plot: PlotConfigModel = Field(
        PlotConfigModel(),
        description='Configuration for the plotting subcommand')
    submit: SubmitConfigModel = Field(
        SubmitConfigModel(),
        description='Configuration for the submit subcommand')
    create: CreateConfigModel = Field(
        CreateConfigModel(),
        description='Configuration for the create subcommand')
    status: StatusConfigModel = Field(
        StatusConfigModel(),
        description='Configuration for the status subcommand')
    workspace: WorkDirectoryModel = WorkDirectoryModel()
    system: Literal['jetto',
                    'dummy'] = Field('jetto',
                                     description='backend system to use')
