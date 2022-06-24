from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from typing_extensions import Literal

from duqtools.config.basemodel import BaseModel

if TYPE_CHECKING:
    from .ids import IDSMapping

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
        logger.info('Apply `%s(%s, %s)`' %
                    (self.ids, self.operator, self.value))

        profile = ids_mapping.flat_fields[self.ids]

        logger.debug('data range before: %s - %s' %
                     (profile.min(), profile.max()))
        self._npfunc(profile, self.value, out=profile)
        logger.debug('data range after: %s - %s' %
                     (profile.min(), profile.max()))

    @property
    def _npfunc(self):
        """Grab numpy function."""
        return getattr(np, self.operator)
