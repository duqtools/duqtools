from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from pydantic import Field, PrivateAttr, field_validator

from ._basemodel import BaseModel
from ._description_helpers import formatter as f


class CreateConfigModel(BaseModel):
    """The options of the `create` subcommand are stored in the `create` key in
    the config."""
    runs_dir: Optional[Path] = Field(
        None,
        description=
        f("""Relative location from the workspace, which specifies the folder where to
        store all the created runs.

        This defaults to `workspace/duqtools_experiment_x`
        where `x` is a not yet existing integer."""))

    template: Optional[Path] = Field(None,
                                     description=f("""
        Template directory to modify. Duqtools copies and updates the settings
        required for the specified system from this directory. This can be a
        directory with a finished run, or one just stored by JAMS (but not yet
        started). By default, duqtools extracts the input IMAS database entry
        from the settings file (e.g. jetto.in) to find the data to modify for
        the UQ runs. Defaults to None.
        """))

    template_data: Optional[ImasBaseModel] = Field(None,
                                                   description=f("""
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
                   CartesianProduct] = Field(discriminator='method',
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

    data: Optional[DataLocation] = Field(None,
                                         description=f("""
        Required for system `jetto-v210921`, ignored for other systems.

        Where to store the in/output IDS data.
        The data key specifies the machine or imas
        database name where to store the data (`imasdb`). duqtools will write the input
        data files for UQ start with the run number given by `run_in_start_at`.
        The data generated by the UQ runs (e.g. from jetto) will be stored
        starting by the run number given by `run_out_start_at`.

        """))

    @field_validator('sampler')
    def default_system(cls, v):
        if v is None:
            from .matrix_samplers import CartesianProduct
            v = CartesianProduct()
        return v


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
        description='Options specific to the system used',
        discriminator='name')

    quiet: bool = Field(
        False,
        description=
        'If true, do not output to stdout, except for mandatory prompts.')

    _path: Union[Path, str] = PrivateAttr(None)

    @field_validator('system')
    def default_system(cls, v):
        if v is None:
            from ..systems.no_system import NoSystemModel
            v = NoSystemModel()
        return v


from ..systems.ets import Ets6SystemModel  # noqa
from ..systems.jetto import JettoSystemModel  # noqa
from ..systems.no_system import NoSystemModel  # noqa
from ._dimensions import CoupledDim, Operation, OperationDim  # noqa
from ._imas import ImasBaseModel  # noqa
from .data_location import DataLocation  # noqa
from .matrix_samplers import (  # noqa
    CartesianProduct, HaltonSampler, LHSSampler, SobolSampler,
)
from .variables import VariableConfigModel  # noqa

CreateConfigModel.update_forward_refs()
ConfigModel.update_forward_refs()
