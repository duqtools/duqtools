from __future__ import annotations

from typing import List, Tuple, Union

import numpy as np
from pydantic import Field, validator
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
    scale_to_error: bool = Field(False,
                                 description=f("""
        If True, multiply value(s) by the error (sigma).

        With asymmetric errors (i.e. both lower/upper error are available),
        scale negative values to the lower error, and positive values to upper
        error.
        """))

    _upper_suffix: str = '_error_upper'
    _lower_suffix: str = '_error_lower'


class IDSOperation(IDSPathMixin, IDSOperatorMixin, BaseModel):
    """Apply arithmetic operation to IDS."""

    value: float = Field(description=f("""
        Values to use with operator on field to create sampling
        space."""))


class LinSpace(BaseModel):
    """Generated evenly spaced numbers over a specified interval.

    See the implementation of [numpy.linspace][] for more details.
    """
    start: float = Field(None, description='Start value of the sequence.')
    stop: float = Field(None, description='End value of the sequence.')
    num: int = Field(None, description='Number of samples to generate.')

    @property
    def values(self):
        """Convert to list."""
        # `val.item()` converts to native python types
        return [
            val.item() for val in np.linspace(self.start, self.stop, self.num)
        ]


class ARange(BaseModel):
    """Generate evenly spaced numbers within a given interval.

    See the implementation of [numpy.arange][] for more details.
    """

    start: float = Field(
        None, description='Start of the interval. Includes this value.')
    stop: float = Field(
        None, description='End of the interval. Excludes this interval.')
    step: float = Field(None, description='Spacing between values.')

    @property
    def values(self):
        """Convert to list."""
        # `val.item()` converts to native python types
        return [
            val.item() for val in np.arange(self.start, self.stop, self.step)
        ]


class IDSOperationDim(IDSPathMixin, IDSOperatorMixin, BaseModel):
    """Apply set of arithmetic operations to IDS.

    Takes the IDS data and subtracts, adds, multiplies, etc with each
    the given values.
    """

    values: Union[List[float], ARange, LinSpace, ] = Field([1.1, 1.2, 1.3],
                                                           description=f("""
            Values to use with operator on field to create sampling
            space."""))

    def expand(self, *args, **kwargs) -> Tuple[IDSOperation, ...]:
        """Expand list of values into operations with its components."""
        return tuple(
            IDSOperation(ids=self.ids,
                         operator=self.operator,
                         value=value,
                         scale_to_error=self.scale_to_error)
            for value in self.values)

    @validator('values')
    def convert_to_list(cls, v):
        if not isinstance(v, list):
            v = v.values
        return v
