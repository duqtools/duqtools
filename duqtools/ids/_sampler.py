from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

import numpy as np
from pydantic import Field
from typing_extensions import Literal

from duqtools.config.basemodel import BaseModel

from ._operation import IDSPathMixin

if TYPE_CHECKING:
    from .ids import IDSMapping

logger = logging.getLogger(__name__)


class IDSSamplerMixin(BaseModel):
    # these follow the same api as normal: gumbel, laplace, logistic, uniform
    sampling: Literal['normal'] = Field('normal',
                                        description='Sampling method.')
    bounds: Literal['symmetric', 'asymmetric'] = Field(
        'symmetric', description='Use symmetric or asymmetric sampling.')
    upper: str = Field('_error_upper',
                       description='Suffix appended to the ids '
                       'to access upper error values')
    lower: Optional[str] = Field(
        None,
        description='Suffix appended to the ids '
        'to access lower error values. Defaults to `upper` if not defined.')


class IDSSampler(IDSPathMixin, IDSSamplerMixin, BaseModel):
    # seed: int = Field(description='Random seed for the sampler')

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
        sigma_upper = abs(upper - profile)

        if self.lower:
            lower = ids_mapping.flat_fields[self.ids + self.lower]
            sigma_lower = abs(profile - lower)
        else:
            sigma_lower = sigma_upper

        # this is only ever necessary if upper/lower are different
        if self.bounds == 'symmetric':
            mean_sigma = (sigma_upper + sigma_lower) / 2
        elif self.bounds == 'asymmetric':
            raise NotImplementedError

        new_profile = np.random.normal(loc=profile, scale=mean_sigma)

        # update in-place
        profile[:] = new_profile


class IDSSamplerSet(IDSPathMixin, IDSSamplerMixin, BaseModel):
    n_samples: int = Field(5, description='Number of samples to get.')

    def expand(self):
        return tuple(
            IDSSampler(ids=self.ids,
                       sampling=self.sampling,
                       bounds=self.bounds,
                       upper=self.upper,
                       lower=self.lower) for _ in range(self.n_samples))
