from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Tuple

import numpy as np
from pydantic import Field
from typing_extensions import Literal

from duqtools.config.basemodel import BaseModel

if TYPE_CHECKING:
    from .ids import IDSMapping

logger = logging.getLogger(__name__)


class IDSPathMixin(BaseModel):
    ids: str = Field(
        'profiles_1d/0/t_i_average',
        description='Field within ids described in template dir from which '
        'to sample.')


class IDSOperatorMixin(BaseModel):
    operator: Literal['add', 'multiply', 'divide', 'power', 'subtract',
                      'floor_divide', 'mod', 'remainder'] = Field(
                          'multiply',
                          description='Operation applied to the ids')
    # factor: Optional[Union[int, str]] = None


class IDSOperation(IDSPathMixin, IDSOperatorMixin, BaseModel):
    value: float = Field(
        description='values to use with operator on field to create sampling'
        ' space')

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
    values: List[float] = Field(
        [1.1, 1.2, 1.3],
        description='Values to use with operator on field to create sampling'
        ' space.')

    def expand(self, *args, **kwargs) -> Tuple[IDSOperation, ...]:
        """Expand list of values into operations with its components."""
        return tuple(
            IDSOperation(ids=self.ids, operator=self.operator, value=value)
            for value in self.values)
