from __future__ import annotations

import logging
from typing import List, Optional, Union

import yaml
from pydantic import BaseModel, DirectoryPath, Field
from typing_extensions import Literal

from duqtools.ids.ids_location import ImasLocation

from ._types import PathLike

logger = logging.getLogger(__name__)


class Plot(BaseModel):
    x: Optional[str]
    # TODO, make y axis time-variable by replacing "0" with "*" for example
    y: str = 'profiles_1d/0/electrons/density_thermal'

    xlabel: Optional[str]
    ylabel: Optional[str]

    add_time_slider: bool = False

    def get_xlabel(self):
        return self.xlabel if self.xlabel else self.x

    def get_ylabel(self):
        return self.ylabel if self.ylabel else self.y


class PlotConfig(BaseModel):
    data: List[ImasLocation] = [
        ImasLocation(**{
            'db': 'jet',
            'shot': 94875,
            'run': 251,
            'user': 'g2vazizi'
        })
    ]
    plots: List[Plot] = [Plot()]


class StatusConfig(BaseModel):
    """Status_config."""

    msg_completed: str = 'Status : Completed successfully'
    msg_failed: str = 'Status : Failed'
    msg_running: str = 'Status : Running'


class SubmitConfig(BaseModel):
    """Submit_config.

    Config class for submitting jobs
    """

    submit_script_name: str = '.llcmd'
    status_file: str = 'jetto.status'
    submit_command: List[str] = ['sbatch']


class Variable(BaseModel):
    source: Literal['jetto.in', 'jetto.jset']
    key: str
    values: list

    def expand(self):
        return tuple({
            'source': self.source,
            'key': self.key,
            'value': value
        } for value in self.values)


class IDSOperation(BaseModel):
    ids: str
    operator: Literal['add', 'multiply', 'divide', 'power', 'subtract',
                      'floor_divide', 'mod', 'remainder']
    values: List[float]

    def expand(self):
        return tuple({
            'ids': self.ids,
            'operator': self.operator,
            'value': value
        } for value in self.values)


class DataLocation(BaseModel):
    db: str
    run_in_start_at: int
    run_out_start_at: int


class LHSSampler(BaseModel):
    method: Literal['latin-hypercube']
    n_samples: int

    def __call__(self, *args):
        from duqtools.samplers import latin_hypercube
        return latin_hypercube(*args, n_samples=self.n_samples)


class Halton(BaseModel):
    method: Literal['halton']
    n_samples: int

    def __call__(self, *args):
        from duqtools.samplers import halton
        return halton(*args, n_samples=self.n_samples)


class SobolSampler(BaseModel):
    method: Literal['sobol', 'low-discrepancy-sequence']
    n_samples: int

    def __call__(self, *args):
        from duqtools.samplers import sobol
        return sobol(*args, n_samples=self.n_samples)


class CartesianProduct(BaseModel):
    method: Literal['cartesian-product'] = 'cartesian-product'

    def __call__(self, *args):
        from duqtools.samplers import cartesian_product
        return cartesian_product(*args)


class CreateConfig(BaseModel):
    matrix: List[IDSOperation] = []
    sampler: Union[LHSSampler, Halton, SobolSampler,
                   CartesianProduct] = Field(default=CartesianProduct(),
                                             discriminator='method')
    template: DirectoryPath
    data: DataLocation


class Config(BaseModel):
    """Config class containing all configs, is a singleton and can be used with
    import duqtools.config.Config as Cfg Cfg().<variable you want>"""

    _instance = None

    # pydantic members
    plot: PlotConfig = PlotConfig()
    submit: SubmitConfig = SubmitConfig()
    create: Optional[CreateConfig]
    status: StatusConfig = StatusConfig()
    workspace: DirectoryPath = './workspace'

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Config._instance:
            Config._instance = object.__new__(cls)
        return Config._instance

    def read(self, filename: PathLike):
        """Read config from file."""
        with open(filename, 'r') as f:
            datamap = yaml.safe_load(f)
            logger.debug(datamap)
            BaseModel.__init__(self, **datamap)


cfg = Config()
