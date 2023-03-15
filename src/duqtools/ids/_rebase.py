import logging
from typing import Optional, Sequence, Union

import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)


def rezero_time(ds: xr.Dataset, *, start: int = 0) -> None:
    """Standardize the time within a dataset by setting the first timestep to 0.

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


def squash_placeholders(ds: xr.Dataset) -> xr.Dataset:
    """Squash placeholder variables. Data are grouped along the first dimension
    (usually time).

    If the data contains dimensions with a `$`-prefix,
    these are all interpolated to the first array of that type.

    Parameters
    ----------
    ds : xr.Dataset
        xarray Dataset

    Returns
    -------
    ds : xr.Dataset
        xarray Dataset
    """
    prefix = '$'

    dimensions = tuple(str(dim) for dim in ds.dims)

    placeholder_vars = [dim for dim in dimensions if dim.startswith(prefix)]

    for var in placeholder_vars:
        new_dim = var.lstrip(prefix)

        var_index = dimensions.index(var)
        group_dims = dimensions[:var_index]

        groupby = group_dims[0]

        ds = standardize_grid(ds, new_dim=new_dim, old_dim=var, group=groupby)

    return ds


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


def standardize_grid_and_time(
    datasets: Sequence[xr.Dataset],
    *,
    grid_var: str = 'rho_tor_norm',
    time_var: str = 'time',
    reference_dataset: int = 0,
) -> tuple[xr.Dataset, ...]:
    """Standardize list of datasets by applying standard rebase operations.

    Applies, in sequence:
    1. `rezero_time`
    2. `standardize_grid`
    3. `rebase_on_grid`
    4. `rebase_on_time`

    Parameters
    ----------
    datasets : Sequence[xr.Dataset]
        List of source datasets
    grid_var : str, optional
        Name of the grid dimension (i.e. grid variable)
    time_var : str, optional
        Name of the time dimension (i.e. time variable)
    reference_dataset : int, optional
        The dataset with this index will be used as the reference for rebasing.
        The grid and time coordinates of the other datasets will be rebased
        to the reference.

    Returns
    -------
    tuple[xr.Dataset]
        Tuple of output datasets
    """
    reference_grid = datasets[reference_dataset][grid_var].data

    datasets = tuple(
        rebase_on_grid(ds, coord_dim=grid_var, new_coords=reference_grid)
        for ds in datasets)

    reference_time = datasets[reference_dataset][time_var].data

    datasets = tuple(
        rebase_on_time(ds, time_dim=time_var, new_coords=reference_time)
        for ds in datasets)

    return datasets


def rebase_all_coords(
    datasets: Sequence[xr.Dataset],
    reference_dataset: xr.Dataset,
) -> tuple[xr.Dataset, ...]:
    """Rebase all coords, by applying rebase operations.

    Parameters
    ----------
    datasets : Sequence[xr.Dataset]
        datasets
    reference_dataset : xr.Dataset
        reference_dataset

    Returns
    -------
    tuple[xr.Dataset, ...]
    """

    interp_dict = {
        name: dim
        for name, dim in reference_dataset.coords.items() if dim.size > 1
    }

    return tuple(
        ds.interp(coords=interp_dict, kwargs={'fill_value': 'extrapolate'})
        for ds in datasets)
