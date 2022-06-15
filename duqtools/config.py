from __future__ import annotations

import logging
from typing import List, Optional, Union

import yaml
from pydantic import BaseModel, DirectoryPath, Field
from typing_extensions import Literal

logger = logging.getLogger(__name__)


class Status_config(BaseModel):
    """Status_config."""

    msg_completed: str = 'Status : Completed successfully'
    msg_failed: str = 'Status : Failed'
    msg_running: str = 'Status : Running'


class Submit_config(BaseModel):
    """Submit_config.

    Config class for submitting jobs
    """

    submit_script_name: str = '.llcmd'
    status_file: str = 'jetto.status'


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


class ConfigCreate(BaseModel):
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
    submit: Submit_config = Submit_config()
    create: Optional[ConfigCreate]
    status: Status_config = Status_config()
    workspace: DirectoryPath = './workspace'

    def __init__(self, filename=None):
        """Initialize with optional filename argument."""
        if filename:
            with open(filename, 'r') as f:
                datamap = yaml.safe_load(f)
                logger.debug(datamap)
                BaseModel.__init__(self, **datamap)

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Config._instance:
            Config._instance = object.__new__(cls)
        return Config._instance
