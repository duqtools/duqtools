from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

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

    # factor: Optional[Union[int, str]] = None

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


class IDSSampler(BaseModel):
    ids: str

    # these follow the same api as normal: gumbel, laplace, logistic, uniform
    sampling: Literal['normal'] = 'normal'
    bounds: Literal['symmetric', 'asymmetric'] = 'symmetric'
    upper: str = '_error_upper'
    lower: Optional[str] = None

    def apply(self, ids_mapping: IDSMapping) -> None:
        """Apply operation to IDS. Data are modified in-place.

        Parameters
        ----------
        ids_mapping : IDSMapping
            Core profiles IDSMapping, data to apply operation to.
            Must contain the IDS path.
        """
        logger.info('Apply %s', self)

        profile = ids_mapping.flat_fields[self.ids]

        upper = ids_mapping.flat_fields[self.ids + self.upper]

        if self.lower:
            lower = ids_mapping.flat_fields[self.ids + self.lower]
        else:
            lower = 2 * profile - upper

            # this is only ever necessary if upper/lower are different
            if self.bounds == 'symmetric':
                sigma_upper = abs(profile - lower)
                sigma_lower = abs(profile - upper)
                mean_sigma = (sigma_upper + sigma_lower) / 2
                lower = profile - mean_sigma
                upper = profile - mean_sigma

        if self.bounds == 'asymmetric':
            raise NotImplementedError

        new_profile = np.random.normal(loc=profile, scale=sigma_upper)

        # update in-place
        profile[:] = new_profile


class IDSSamplerSet(BaseModel):
    ids: str

    # these follow the same api as normal: gumbel, laplace, logistic, uniform
    sampling: Literal['normal'] = 'normal'
    bounds: Literal['symmetric', 'asymmetric'] = 'symmetric'
    upper = '_error_upper'
    lower: Optional[str] = None
    n_samples: int = 5

    def expand(self):
        return tuple(
            IDSSampler(ids=self.ids,
                       sampling=self.sampling,
                       bounds=self.bounds,
                       upper=self.upper,
                       lower=self.lower) for _ in range(self.n_samples))
