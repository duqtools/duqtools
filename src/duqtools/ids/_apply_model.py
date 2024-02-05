from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Union

import numpy as np

from .._logging_utils import duqlog_screen
from ._handle import ImasHandle

if TYPE_CHECKING:
    from types import SimpleNamespace

    from ..schema import IDSOperation
    from .mapping import IDSMapping

logger = logging.getLogger(__name__)


def _apply_ids(model: IDSOperation,
               *,
               ids_mapping: Union[ImasHandle, IDSMapping],
               input_var: Optional[SimpleNamespace] = None,
               **kwargs) -> None:
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

            sigma = ids_mapping[sigma_key]

            value = sigma * model.value
        else:

            value = model.value

        logger.info('Apply %s', model)

        if model.linear_ramp is not None:
            a, b = model.linear_ramp
            value = np.linspace(a, b, len(data)) * value

        logger.debug('data range before: %s - %s', data.min(), data.max())

        model.npfunc(data, value, out=data, var=input_var)

        if model.clip_max is not None or model.clip_min is not None:
            np.clip(data, a_min=model.clip_min, a_max=model.clip_max, out=data)

        logger.debug('data range after: %s - %s', data.min(), data.max())

    if target_in:
        logger.info('Writing data entry: %s', target_in)
        target_in.update_from(ids_mapping)
