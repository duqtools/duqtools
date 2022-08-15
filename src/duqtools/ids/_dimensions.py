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
    if isinstance(model.variable, str):
        raise TypeError('`model.variable` must have a `path` attribute.')

    npfunc = getattr(np, model.operator)

    data_map = ids_mapping.findall(model.variable.path)

    for path, data in data_map.items():
        if model.scale_to_error:
            sigma_key = path + model._upper_suffix

            if model.value < 0:
                lower_key = path + model._lower_suffix
                if lower_key in ids_mapping:
                    sigma_key = lower_key

            if sigma_key not in ids_mapping:
                raise ValueError(f'scale_to_error={model.scale_to_error} '
                                 f'but `{sigma_key}` is empty.')

            sigma_bound = ids_mapping[sigma_key]
            sigma = abs(sigma_bound - data)

            value = sigma * model.value
        else:

            value = model.value

        logger.info('Apply %s', model)

        logger.debug('data range before: %s - %s', data.min(), data.max())
        npfunc(data, value, out=data)
        logger.debug('data range after: %s - %s', data.min(), data.max())
