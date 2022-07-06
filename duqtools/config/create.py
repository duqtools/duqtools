from __future__ import annotations

from typing import List, Union

from pydantic import DirectoryPath, Field
from typing_extensions import Literal

from duqtools.ids import IDSOperationSet, IDSSamplerSet

from .basemodel import BaseModel


class DataLocation(BaseModel):
    db: str = 'jet'
    run_in_start_at: int = 7000
    run_out_start_at: int = 8000


class LHSSampler(BaseModel):
    method: Literal['latin-hypercube'] = Field(
        'latin-hypercube',
        description='Method to select samples, default: latin-hypercube, also'
        ' supports: halton, sobol, cartesian-product')
    n_samples: int = Field(3, description='Number of samples to take')

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
    matrix: List[Union[IDSOperationSet, IDSSamplerSet]] = Field(
        [IDSOperationSet()], description='Defines the space to sample')
    sampler: Union[LHSSampler, Halton, SobolSampler,
                   CartesianProduct] = Field(default=LHSSampler(),
                                             discriminator='method')
    template: DirectoryPath = Field(
        '/pfs/work/g2ssmee/jetto/runs/duqtools_template',
        description='jetto run-case to use as template for all the other runs')
    data: DataLocation = Field(
        DataLocation(), description='Where to store the in/output IDS data')
