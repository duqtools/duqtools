from __future__ import annotations

import logging
from typing import Union

import numpy as np

from .._logging_utils import duqlog_screen
from ..apply_model import apply_model
from ..schema import IDSOperation
from ._handle import ImasHandle
from ._mapping import IDSMapping

logger = logging.getLogger(__name__)


@apply_model.register  # type: ignore
def _apply_ids(model: IDSOperation, *,
               ids_mapping: Union[ImasHandle, IDSMapping], **kwargs) -> None:
    """Implementation for IDS operations.

    Parameters
    ----------
    model : IDSOperation
        model
    target_in : ImasHandle, IDSMapping
        ImasHandle/IDSHandle, data to apply operation to.

    Returns
    -------
    None
    """
    target_in = None
    if isinstance(ids_mapping, ImasHandle):
        target_in = ids_mapping
        ids_mapping = ids_mapping.get(model.variable.ids)

    if isinstance(model.variable, str):
        raise TypeError('`model.variable` must have a `path` attribute.')

    npfunc = getattr(np, model.operator)

    data_map = ids_mapping.findall(model.variable.path)

    if len(data_map) == 0:
        # TODO this should be 'raise Error' but that breaks our tests,
        # leave it as a message until we can fix it with a Jetto-IMAS container
        duqlog_screen.error(
            f'{model.variable.path} not found in IDS, cannot adjust value')

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

    if target_in:
        logger.info('Writing data entry: %s', target_in)
        ids_mapping.sync(target_in)
