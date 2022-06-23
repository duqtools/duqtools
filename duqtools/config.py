from __future__ import annotations

import logging
from getpass import getuser
from pathlib import Path
from typing import List, Optional, Tuple, Union

import yaml
from pydantic import DirectoryPath, Field, validator
from typing_extensions import Literal

from ._types import PathLike
from .basemodel import BaseModel
from .ids import IDSOperation

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
    out_file: str = 'jetto.out'
    in_file: str = 'jetto.in'
    submit_command: List[str] = ['sbatch']


class IDSOperationSet(BaseModel):
    ids: str = 'profiles_1d/0/t_i_average'
    operator: Literal['add', 'multiply', 'divide', 'power', 'subtract',
                      'floor_divide', 'mod', 'remainder'] = 'multiply'
    values: List[float] = [1.1, 1.2, 1.3]

    def expand(self) -> Tuple[IDSOperation, ...]:
        """Expand list of values into operations with its components."""
        return tuple(
            IDSOperation(ids=self.ids, operator=self.operator, value=value)
            for value in self.values)


class DataLocation(BaseModel):
    db: str = 'jet'
    run_in_start_at: int = 7000
    run_out_start_at: int = 8000


class LHSSampler(BaseModel):
    method: Literal['latin-hypercube']
    n_samples: int = 3

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
    matrix: List[IDSOperationSet] = [IDSOperationSet()]
    sampler: Union[LHSSampler, Halton, SobolSampler,
                   CartesianProduct] = Field(default=CartesianProduct(),
                                             discriminator='method')
    template: DirectoryPath = '/pfs/work/g2ssmee/jetto/runs/duqtools_template'
    data: DataLocation = DataLocation()


class WorkDirectory(BaseModel):
    root: DirectoryPath = f'/pfs/work/{getuser()}/jetto/runs/'

    @property
    def cwd(self):
        cwd = Path.cwd()
        if not cwd.relative_to(self.root):
            raise IOError(
                f'Work directory must be a subdirectory of {self.root}')
        return cwd

    @property
    def subdir(self):
        """Get subdirectory relative to root."""
        return self.cwd.relative_to(self.root)

    @validator('root')
    def resolve_root(cls, v):
        return v.resolve()

    @property
    def runs_yaml(self):
        """Location of runs.yaml."""
        return self.cwd / 'runs.yaml'


class Config(BaseModel):
    """Config class containing all configs, is a singleton and can be used with
    import duqtools.config.Config as Cfg Cfg().<variable you want>"""

    _instance = None

    plot: PlotConfig = PlotConfig()
    submit: SubmitConfig = SubmitConfig()
    create: CreateConfig = CreateConfig()
    status: StatusConfig = StatusConfig()
    workspace: WorkDirectory = WorkDirectory()

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
