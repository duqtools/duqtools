from typing import List, Tuple, Union

from pydantic import DirectoryPath, Field
from typing_extensions import Literal

from duqtools.ids import IDSOperation

from .basemodel import BaseModel


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
