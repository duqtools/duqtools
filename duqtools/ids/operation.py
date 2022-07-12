from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Tuple

import numpy as np
from pydantic import Field
from typing_extensions import Literal

from duqtools.config.basemodel import BaseModel

from ..config._description_helpers import formatter as f

if TYPE_CHECKING:
    from .ids import IDSMapping

logger = logging.getLogger(__name__)


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


class IDSOperationSet(IDSPathMixin, IDSOperatorMixin, BaseModel):
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
