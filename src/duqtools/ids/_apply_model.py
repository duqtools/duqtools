from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

import numpy as np
from imas2xarray import to_imas, to_xarray

from ._handle import ImasHandle

if TYPE_CHECKING:
    from types import SimpleNamespace

    from ..schema import IDSOperation

logger = logging.getLogger(__name__)


def _apply_ids(model: IDSOperation,
               *,
               handle: ImasHandle,
               input_var: Optional[SimpleNamespace] = None,
               **kwargs) -> None:
    """Implementation for IDS operations.

    Parameters
    ----------
    model : IDSOperation
        model
    handle : ImasHandle
        Data to apply operation to.

    Returns
    -------
    None
    """
    assert isinstance(handle, ImasHandle)

    dataset = to_xarray(handle.path(),
                        ids=model.variable.ids,
                        variables=(model.variable.name, ))

    if isinstance(model.variable, str):
        raise TypeError('`model.variable` must have a `path` attribute.')

    dataarray = dataset[model.variable.name]

    if model.scale_to_error:
        sigma_key = path + model._upper_suffix

        if model.value < 0:
            lower_key = path + model._lower_suffix
            if lower_key in handle:
                sigma_key = lower_key

        if sigma_key not in handle:
            raise ValueError(f'scale_to_error={model.scale_to_error} '
                             f'but `{sigma_key}` is empty.')

        sigma = handle[sigma_key]

        value = sigma * model.value
    else:
        value = model.value

    logger.info('Apply %s', model)

    if model.linear_ramp is not None:
        a, b = model.linear_ramp
        value = np.linspace(a, b, len(dataarray)) * value

    logger.debug('data range before: %s - %s', dataarray.min(),
                 dataarray.max())

    dataset[model.variable.name] = model.npfunc(dataarray,
                                                value,
                                                var=input_var)

    if model.clip_max is not None or model.clip_min is not None:
        np.clip(dataarray,
                a_min=model.clip_min,
                a_max=model.clip_max,
                out=dataarray)

    logger.debug('data range after: %s - %s', dataarray.min(), dataarray.max())

    logger.info('Writing data entry: %s', handle)

    dataset = to_imas(handle.path(),
                      dataset=dataset,
                      ids=model.variable.ids,
                      variables=(model.variable.name, ))
