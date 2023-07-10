from __future__ import annotations

from typing import Literal

from pydantic import Field

from ._basemodel import BaseModel


class LHSSampler(BaseModel):
    """Select the Latin Hypercube sampler by specifying `method: latin-
    hypercube`."""

    method: Literal['latin-hypercube'] = 'latin-hypercube'

    n_samples: int = Field(3, description='Number of samples to take')


class HaltonSampler(BaseModel):
    """Select the Sobol sampler by specifying `method: halton`."""

    method: Literal['halton']

    n_samples: int = Field(3, description='Number of samples to take')


class SobolSampler(BaseModel):
    """Select the Sobol sampler by specifying `method: sobol`."""

    method: Literal['sobol', 'low-discrepancy-sequence']

    n_samples: int = Field(3, description='Number of samples to take')


class CartesianProduct(BaseModel):
    """Select the Cartesian product sampler by specifying `method: cartesian-
    product`."""

    method: Literal['cartesian-product'] = 'cartesian-product'
