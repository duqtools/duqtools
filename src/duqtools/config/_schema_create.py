from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from pydantic import Field

from duqtools.schema import BaseModel
from duqtools.utils import formatter as f

from ..ids._schema import ImasBaseModel
from ..schema import CoupledDim, Operation, OperationDim
from ..schema.matrix_samplers import (
    CartesianProduct,
    HaltonSampler,
    LHSSampler,
    SobolSampler,
)


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
                   CartesianProduct] = Field(CartesianProduct(),
                                             discriminator='method',
                                             description=f("""
        For efficient UQ, it may not be necessary to sample the entire matrix
        or hypercube. By default, the cartesian product is taken
        (`method: cartesian-product`). For more efficient sampling of the space,
        the following `method` choices are available:
        [`latin-hypercube`](https://en.wikipedia.org/wiki/Latin_hypercube_sampling),
        [`sobol`](https://en.wikipedia.org/wiki/Sobol_sequence),
        [`halton`](https://en.wikipedia.org/wiki/Halton_sequence).
        Where `n_samples` gives the number of samples to extract.
        """))

    dimensions: list[Union[CoupledDim, OperationDim]] = Field(default=[],
                                                              description=f("""
        The `dimensions` specifies the dimensions of the matrix to sample
        from. Each dimension is a compound set of operations to apply.
        From this, a matrix all possible combinations is generated.
        Essentially, it generates the
        [Cartesian product](https://en.wikipedia.org/wiki/Cartesian_product)
        of all operations. By specifying a different `sampler`, a subset of
        this hypercube can be efficiently sampled. This paramater is optional.
        """))
