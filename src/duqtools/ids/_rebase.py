import logging
from typing import List, Optional, Sequence, Union

import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)


def standardize_time(ds: xr.Dataset, *, start: int = 0) -> None:
    """Standardize the time within a dataset.

    Simply subtracts time[0] from all time entries and adds `start`
    Note: this does not interpolate the times between different datasets

    Parameters
    ----------
    ds : xr.Dataset
        Source dataset
    start : int, optional
        Where to start the returned time series
    """

    ds['time'] = ds['time'] - ds['time'][0] + start


def standardize_grid(ds: xr.Dataset,
                     *,
                     new_dim: str,
                     old_dim: str,
                     group: Optional[str] = None,
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
        new_dim_data = ds.isel(  # type: ignore
            **{group: new_dim_data})[new_dim].data  # type:ignore

    gb = ds.groupby(group)

    interp_kwargs = {new_dim: new_dim_data}

    def standardize(group):
        group = group.swap_dims({old_dim: new_dim})
        group = group.interp(**interp_kwargs)
        return group

    return gb.map(standardize)


def rebase_on_grid(ds: xr.Dataset, *, coord_dim: str,
                   new_coords: np.ndarray) -> xr.Dataset:
    """Rebase (interpolate) the coordinate dimension to the new coordinates.

    Thin wrapper around `xarray.Dataset.interp`.

    Parameters
    ----------
    ds : xr.Dataset
        Source dataset
    coord_dim : str
        Name of the grid dimension (i.e. grid variable).
    new_coords : np.ndarray
        The coordinates to interpolate to

    Returns
    -------
    xr.Dataset
        Rebased dataset
    """
    return ds.interp(coords={coord_dim: new_coords},
                     kwargs={'fill_value': 'extrapolate'})


def rebase_on_time(ds: xr.Dataset,
                   *,
                   time_dim='time',
                   new_coords: np.ndarray) -> xr.Dataset:
    """Rebase (interpolate) the time dimension to the new coordinates.

    Thin wrapper around `xarray.Dataset.interp`.

    Parameters
    ----------
    ds : xr.Dataset
        Source dataset
    time_dim : str
        Name of the time dimension (i.e. time variable).
    new_coords : np.ndarray
        The coordinates to interpolate to

    Returns
    -------
    xr.Dataset
        Rebased dataset
    """
    if len(ds[time_dim]) < 2:
        # nothing to rebase with only 1 timestep
        return ds
    else:
        return rebase_on_grid(ds, coord_dim=time_dim, new_coords=new_coords)


def standardize_datasets(
    datasets: Sequence[xr.Dataset],
    *,
    grid_var: str = 'rho_tor_norm',
    grid_placeholder: str = 'x',
    time_var: str = 'time',
    reference_grid_idx: int = 0,
    reference_dataset: int = 0,
) -> List[xr.Dataset]:
    """Standardize list of datasets by applying standard rebase operations.

    Applies, in sequence:
    1. `standardize_grid`
    2. `rebase_on_grid`
    3. `rebase_on_time`

    Parameters
    ----------
    datasets : Sequence[xr.Dataset]
        List of source datasets
    grid_var : str, optional
        Name of the grid dimension (i.e. grid variable)
    grid_placeholder : str, optional
        Name of the placeholder for the grid dimension
    time_var : str, optional
        Name of the time dimension (i.e. time variable)
    reference_grid_idx : int, optional
        For each dataset, the data of the grid with this index along the time dimension
        will be used as the new coordinate for the grid dimension. Data variables will
        be rebased onto these coordinates if necessary.

        Maps to `new_dim_data` in `standardize_grid`.
    reference_dataset : int, optional
        The dataset with this index will be used as the reference for rebasing.
        The grid and time coordinates of the other datasets will be rebased
        to the reference.

    Returns
    -------
    List[xr.Dataset]
        List of output datasets
    """
    datasets = [
        standardize_grid(
            ds,
            new_dim=grid_var,
            old_dim=grid_placeholder,
            new_dim_data=reference_grid_idx,
            group=time_var,
        ) for ds in datasets
    ]

    reference_grid = datasets[reference_dataset][grid_var].data

    datasets = [
        rebase_on_grid(ds, coord_dim=grid_var, new_coords=reference_grid)
        for ds in datasets
    ]

    reference_time = datasets[reference_dataset][time_var].data

    datasets = [
        rebase_on_time(ds, time_dim=time_var, new_coords=reference_time)
        for ds in datasets
    ]

    return datasets
