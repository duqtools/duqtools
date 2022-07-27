from __future__ import annotations

import logging
from functools import singledispatch

import numpy as np

from ..schema import BaseModel, IDSOperation
from ._mapping import IDSMapping

logger = logging.getLogger(__name__)


@singledispatch
def apply_model(model: BaseModel, ids_mapping: IDSMapping) -> None:
    """Apply operation in model to IDS. Data are modified in-place.

    Parameters
    ----------
    model
        The model describes the operation to apply to the data.
    ids_mapping : IDSMapping
        Core profiles IDSMapping, data to apply operation to.
        Must contain the IDS path.

    Raises
    ------
    NotImplementedError
        When the model is unknown
    """

    raise NotImplementedError(f'Unknown model: {model}')


@apply_model.register
def _(model: IDSOperation, ids_mapping: IDSMapping) -> None:

    npfunc = getattr(np, model.operator)

    profile = ids_mapping.flat_fields[model.ids]

    if model.scale_to_error:
        sigma_key = model.ids + model._upper_suffix

        if model.value < 0:
            lower_key = model.ids + model._lower_suffix
            if lower_key in ids_mapping.flat_fields:
                sigma_key = lower_key

        sigma_bound = ids_mapping.flat_fields[sigma_key]
        sigma = abs(sigma_bound - profile)

        value = sigma * model.value
    else:
        value = model.value

    logger.info('Apply %s', model)

    logger.debug('data range before: %s - %s', profile.min(), profile.max())
    npfunc(profile, value, out=profile)
    logger.debug('data range after: %s - %s', profile.min(), profile.max())
