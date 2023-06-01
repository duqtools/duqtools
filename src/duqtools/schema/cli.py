from pathlib import Path
from typing import Literal, Optional, Union

from pydantic import DirectoryPath, Field, PrivateAttr

from ._basemodel import BaseModel
from ._description_helpers import formatter as f
from ._dimensions import CoupledDim, Operation, OperationDim
from ._imas import ImasBaseModel
from ._systems import DummySystemModel, Ets6SystemModel, JettoSystemModel
from .data_location import DataLocation
from .matrix_samplers import CartesianProduct, HaltonSampler, LHSSampler, SobolSampler
from .variables import VariableConfigModel


class CreateConfigModel(BaseModel):
    """The options of the `create` subcommand are stored in the `create` key in
    the config."""
    runs_dir: Optional[Path] = Field(description=f(
        """Relative location from the workspace, which specifies the folder where to
        store all the created runs.

        This defaults to `workspace/duqtools_experiment_x`
        where `x` is a not yet existing integer."""))

    template: Path = Field(description=f("""
        Template directory to modify. Duqtools copies and updates the settings
        required for the specified system from this directory. This can be a
        directory with a finished run, or one just stored by JAMS (but not yet
        started). By default, duqtools extracts the input IMAS database entry
        from the settings file (e.g. jetto.in) to find the data to modify for
        the UQ runs.
        """))

    template_data: Optional[ImasBaseModel] = Field(description=f("""
        Specify the location of the template data to modify. This overrides the
        location of the data specified in settings file in the template
        directory.
        """))

    operations: list[Operation] = Field(default=[],
                                        description="""
        These `operations` are always applied to the data.
        All operations specified here are added to any operations sampled
        from the dimensions.
        They can be used to, for example, set the start time for an experiment
        or update some physical parameters.
        This parameter is optional.
        """)

    sampler: Union[LHSSampler, HaltonSampler, SobolSampler,
                   CartesianProduct] = Field(default=CartesianProduct(),
                                             discriminator='method',
                                             description=f("""
        For efficient UQ, it may not be necessary to sample the entire matrix
        or hypercube. By default, the cartesian product is taken
        (`method: cartesian-product`). For more efficient sampling of the space,
        the following `method` choices are available:
        [`latin-hypercube`](en.wikipedia.org/wiki/Latin_hypercube_sampling),
        [`sobol`](en.wikipedia.org/wiki/Sobol_sequence),
        [`halton`](en.wikipedia.org/wiki/Halton_sequence).
        Where `n_samples` gives the number of samples to extract.
        """))

    dimensions: list[Union[CoupledDim, OperationDim]] = Field(default=[],
                                                              description=f("""
        The `dimensions` specifies the dimensions of the matrix to sample
        from. Each dimension is a compound set of operations to apply.
        From this, a matrix all possible combinations is generated.
        Essentially, it generates the
        [Cartesian product](en.wikipedia.org/wiki/Cartesian_product)
        of all operations. By specifying a different `sampler`, a subset of
        this hypercube can be efficiently sampled. This paramater is optional.
        """))

    jruns: Optional[DirectoryPath] = Field(description=f(
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

    data: Optional[DataLocation] = Field(description=f("""
        Required for `system: jetto-v210921`, ignored for other systems.

        Where to store the in/output IDS data.
        The data key specifies the machine or imas
        database name where to store the data (`imasdb`). duqtools will write the input
        data files for UQ start with the run number given by `run_in_start_at`.
        The data generated by the UQ runs (e.g. from jetto) will be stored
        starting by the run number given by `run_out_start_at`.

        """))


class SubmitConfigModel(BaseModel):
    """The options of the `submit` subcommand are stored under the `submit` key
    in the config.

    The config describes the commands to start the UQ runs.
    """

    submit_system: Literal['prominence', 'slurm', 'docker'] = Field(
        'slurm',
        description='System to submit jobs to '
        '[slurm (default), prominence, docker]')
    submit_command: str = Field('sbatch',
                                description='Submission command for slurm.')
    docker_image: str = Field('jintrac-imas',
                              description='Docker image used for submission')


class StatusConfigModel(BaseModel):
    """The options of the `status` subcommand are stored under the `status` key
    in the config.

    These only need to be changed if the modeling software changes.
    """
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


class ConfigModel(BaseModel):
    """The options for the CLI are defined by this model."""
    tag: str = Field(
        '',
        description=
        'Create a tag for the runs to identify them in slurm or `data.csv`')

    submit: SubmitConfigModel = Field(
        SubmitConfigModel(),
        description=
        'Configuration for the submit subcommand. See model for more info.')

    create: Optional[CreateConfigModel] = Field(
        description=
        'Configuration for the create subcommand. See model for more info.')

    status: StatusConfigModel = Field(
        StatusConfigModel(),
        description=
        'Configuration for the status subcommand. See model for more info.')

    extra_variables: Optional[VariableConfigModel] = Field(
        description='Specify extra variables for this run.')

    system: Union[DummySystemModel, Ets6SystemModel, JettoSystemModel] = Field(
        JettoSystemModel(),
        description='Options specific to the system used',
        discriminator='name')

    quiet: bool = Field(
        False,
        description=
        'If true, do not output to stdout, except for mandatory prompts.')

    _path: Union[Path, str] = PrivateAttr(None)
