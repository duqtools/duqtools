from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from pydantic import Field
from typing_extensions import Literal

from duqtools.config.basemodel import BaseModel

from ..config._description_helpers import formatter as f
from ..utils import dry_run_toggle
from .operation import IDSPathMixin

if TYPE_CHECKING:
    from .ids import IDSMapping

logger = logging.getLogger(__name__)


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
    _lower_suffix: str = '_error_upper'


class IDSSampler(IDSPathMixin, IDSSamplerMixin, BaseModel):
    """Sample from IDS between error bounds."""

    @dry_run_toggle
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
