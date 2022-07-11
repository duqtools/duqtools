from __future__ import annotations

import logging
from typing import TYPE_CHECKING

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
    bounds: Literal['symmetric', 'asymmetric', 'auto'] = Field(
        'auto',
        description='Specify `symmetric` or `asymmetric` sampling. Use `auto`'
        ' to choose `asymmetric` if the lower bounds are defined,'
        ' else `symmetric`.')

    _upper_suffix: str = '_error_upper'
    _lower_suffix: str = '_error_upper'


class IDSSampler(IDSPathMixin, IDSSamplerMixin, BaseModel):

    def apply(self, ids_mapping: IDSMapping) -> None:
        """Apply operation to IDS. Data are modified in-place.

        Parameters
        ----------
        ids_mapping : IDSMapping
            Core profiles IDSMapping, data to apply operation to.
            Must contain the IDS path.
        """
        upper_key = self.ids + self._upper_suffix
        lower_key = self.ids + self._lower_suffix

        logger.info('Apply %s', self)

        profile = ids_mapping.flat_fields[self.ids]

        upper = ids_mapping.flat_fields[upper_key]
        sigma_upper = abs(upper - profile)

        has_lower = lower_key in ids_mapping.flat_fields

        if self.bounds == 'auto':
            bounds = 'asymmetric' if has_lower else 'symmetric'
        else:
            bounds = self.bounds

        # this is only ever necessary if upper/lower are different
        if bounds == 'symmetric':

            if has_lower:
                lower = ids_mapping.flat_fields[lower_key]
                sigma_lower = abs(profile - lower)
                mean_sigma = (sigma_upper + sigma_lower) / 2
            else:
                mean_sigma = sigma_upper

            rng = np.random.default_rng()
            new_profile = rng.normal(loc=profile, scale=mean_sigma)

        elif bounds == 'asymmetric':
            raise NotImplementedError
        else:
            raise ValueError(
                f'Unknown value for argument: bounds={self.bounds}')

        # update in-place
        profile[:] = new_profile


class IDSSamplerSet(IDSPathMixin, IDSSamplerMixin, BaseModel):
    n_samples: int = Field(5, description='Number of samples to get.')

    def expand(self):
        return tuple(
            IDSSampler(
                ids=self.ids, sampling=self.sampling, bounds=self.bounds)
            for _ in range(self.n_samples))
