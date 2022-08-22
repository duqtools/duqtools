import logging
from typing import Union

import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)


def standardize_grid(ds: xr.Dataset,
                     *,
                     new_dim: str,
                     old_dim: str,
                     group: str = None,
                     new_dim_data: Union[np.ndarray, int] = 0) -> xr.Dataset:
    """Standardize the grid within a dataset.

    Perform `split-apply-combine` routine on the data. Split
    by the `group`, standardize the data in `new_dim` using
    `new_dim_data` (interpolate if necessary),
    and combine replacing `old_dim` by `new_dim`.

    Parameters
    ----------
    ds : xr.Dataset
        Source dataset
    new_dim : str
        Must be an existing variable with `group` as a dimension.
    old_dim : str
        Must be an existing dimension without coordinates.
    group : str, optional
        Split the data in groups over this dimension.
    new_dim_data : Union[np.ndarray, int], optional
        The data to be used for `new_dim`. If it is an integer,
        use it as an index to grab the data from `new_dim`.

    Returns
    -------
    xr.Dataset
        New dataset with `new_dim` as a coordinate dimension.
    """
    if isinstance(new_dim_data, int):
        new_dim_data = ds.isel(**{group: new_dim_data})[new_dim].data

    gb = ds.groupby(group)

    interp_kwargs = {new_dim: new_dim_data}

    def standardize(group):
        group = group.swap_dims({old_dim: new_dim})
        group = group.interp(**interp_kwargs)
        return group

    return gb.map(standardize)


def rebase_on_grid(ds: xr.Dataset, *, coord_dim: str,
                   new_coords: np.ndarray) -> xr.Dataset:
    return ds.interp(coords={coord_dim: new_coords},
                     kwargs={'fill_value': 'extrapolate'})


def rebase_on_time(ds: xr.Dataset,
                   *,
                   time_dim='time',
                   new_coords: np.ndarray) -> xr.Dataset:
    return rebase_on_grid(ds, coord_dim=time_dim, new_coords=new_coords)
