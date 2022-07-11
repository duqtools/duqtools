import logging
from typing import List, Tuple, Union

import numpy as np
from pydantic import DirectoryPath, Field
from typing_extensions import Literal

from duqtools.ids._mapping import IDSMapping

from .basemodel import BaseModel

logger = logging.getLogger(__name__)


class IDSOperation(BaseModel):
    ids: str
    operator: Literal['add', 'multiply', 'divide', 'power', 'subtract',
                      'floor_divide', 'mod', 'remainder']
    value: float

    def apply(self, ids_mapping: IDSMapping) -> None:
        """Apply operation to IDS. Data are modified in-place.

        Parameters
        ----------
        ids_mapping : IDSMapping
            Core profiles IDSMapping, data to apply operation to.
            Must contain the IDS path.
        """
        logger.info('Apply `%s(%s, %s)`', self.ids, self.operator, self.value)

        profile = ids_mapping.flat_fields[self.ids]

        logger.debug('data range before: %s - %s', profile.min(),
                     profile.max())
        self._npfunc(profile, self.value, out=profile)
        logger.debug('data range after: %s - %s', profile.min(), profile.max())

    @property
    def _npfunc(self):
        """Grab numpy function."""
        return getattr(np, self.operator)


class IDSOperationSet(BaseModel):
    ids: str = Field(
        'profiles_1d/0/t_i_average',
        description='field within ids described in template dir from which'
        ' to sample')
    operator: Literal['add', 'multiply', 'divide', 'power', 'subtract',
                      'floor_divide', 'mod', 'remainder'] = Field(
                          'multiply',
                          description='Operation used for sampling')
    values: List[float] = Field(
        [1.1, 1.2, 1.3],
        description='values to use with operator on field to create sampling'
        ' space')

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
    matrix: List[IDSOperationSet] = Field(
        [IDSOperationSet()], description='Defines the space to sample')
    sampler: Union[LHSSampler, Halton, SobolSampler,
                   CartesianProduct] = Field(default=LHSSampler(),
                                             discriminator='method')
    template: DirectoryPath = Field(
        '/pfs/work/g2ssmee/jetto/runs/duqtools_template',
        description='run-case to use as template for all the other runs')
    data: DataLocation = Field(
        DataLocation(), description='Where to store the in/output IDS data')
