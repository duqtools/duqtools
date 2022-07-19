from __future__ import annotations

from typing import List, Tuple

from pydantic import Field
from typing_extensions import Literal

from ._basemodel import BaseModel
from ._description_helpers import formatter as f


class IDSPathMixin(BaseModel):
    ids: str = Field('profiles_1d/0/t_i_average',
                     description=f("""
            IDS Path of the data to modify. `core_profiles` is implied.
            """))


class IDSOperatorMixin(BaseModel):
    operator: Literal['add', 'multiply', 'divide', 'power', 'subtract',
                      'floor_divide', 'mod',
                      'remainder'] = Field('multiply',
                                           description=f("""
        Which operator to apply to the data in combination with any of the
        given values below. This can be any of the basic numpy arithmetic
        operations. Available choices: `add`, `multiply`, `divide`, `power`,
        `subtract`, `floor_divide`, `mod`, and `remainder`. These directly map
        to the equivalent numpy functions, i.e. `add` -> `np.add`.
        """))


class IDSOperation(IDSPathMixin, IDSOperatorMixin, BaseModel):
    """Apply arithmetic operation to IDS."""

    value: float = Field(description=f("""
        Values to use with operator on field to create sampling
        space."""))


class IDSOperationDim(IDSPathMixin, IDSOperatorMixin, BaseModel):
    """Apply set of arithmetic operations to IDS.

    Takes the IDS data and subtracts, adds, multiplies, etc with each
    the given values.
    """

    values: List[float] = Field([1.1, 1.2, 1.3],
                                description=f("""
            Values to use with operator on field to create sampling
            space."""))

    def expand(self, *args, **kwargs) -> Tuple[IDSOperation, ...]:
        """Expand list of values into operations with its components."""
        return tuple(
            IDSOperation(ids=self.ids, operator=self.operator, value=value)
            for value in self.values)


class IDSSamplerMixin(BaseModel):
    # these follow the same api as normal: gumbel, laplace, logistic, uniform
    distribution: Literal['normal'] = Field('normal',
                                            description=f("""
        Sample from given distribution. Currently `normal` is the only option.
                                            """))
    bounds: Literal['symmetric', 'asymmetric',
                    'auto'] = Field('symmetric',
                                    description=f("""
        Specify `symmetric` or `asymmetric` sampling. Use
        `auto` to choose `asymmetric` if the lower bounds are defined,
        else `symmetric`. The bounds are defiend by `$IDS_error_upper`
        and `$IDS_error_lower` in the data specification. Symmetric
        sampling sampling when both the lower and upper error bounds
        are present, takes the average of the two."""))

    _upper_suffix: str = '_error_upper'
    _lower_suffix: str = '_error_lower'


class IDSSampler(IDSPathMixin, IDSSamplerMixin, BaseModel):
    """Sample from IDS between error bounds."""


class IDSSamplerDim(IDSPathMixin, IDSSamplerMixin, BaseModel):
    """This operation samples data between the given error bounds.

    Takes the IDS data from the specified path. The value is taken as
    the mean, and the upper and lower error
    bounds are specified by the `_error_upper` and `_error_lower` suffix.

    Data are sampled from a normal distribution around the mean.

    If the lower error bound is absent, assume a symmetric distribution.
    """

    n_samples: int = Field(5, description='Number of samples to get.')

    def expand(self):
        return tuple(
            IDSSampler(ids=self.ids,
                       distribution=self.distribution,
                       bounds=self.bounds) for _ in range(self.n_samples))
