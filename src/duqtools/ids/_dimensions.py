from __future__ import annotations

import logging
from functools import singledispatch

import numpy as np

from ..schema import BaseModel, IDSOperation, JettoOperation
from ._handle import ImasHandle

logger = logging.getLogger(__name__)


@singledispatch
def apply_model(model: BaseModel, **kwargs) -> None:
    """Apply operation in model to target. Data are modified in-place.

    Parameters
    ----------
    model
        The model describes the operation to apply to the data.

    Raises
    ------
    NotImplementedError
        When the model is unknown
    """

    raise NotImplementedError(f'Unknown model: {model}')


@apply_model.register
def _(model: IDSOperation, *, target_in: ImasHandle, **kwargs) -> None:
    """_. Implementation for IDS operations.

    Parameters
    ----------
    target_in : ImasHandle
        ImasHandle, data to apply operation to.

    Returns
    -------
    None
    """
    ids_mapping = target_in.get(model.variable.ids)
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

    logger.info('Writing data entry: %s', target_in)
    ids_mapping.sync(target_in)


@apply_model.register
def _(model: JettoOperation, **kwargs):
    pass
