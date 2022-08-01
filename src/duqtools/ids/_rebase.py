import logging
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from ._constants import RUN_COL, TIME_COL, TSTEP_COL

logger = logging.getLogger(__name__)


def rebase_on_grid(source: pd.DataFrame,
                   *,
                   grid: str,
                   cols: Sequence[str],
                   grid_base: np.ndarray = None) -> pd.DataFrame:
    """Rebase data on new ids basis using interpolation.

    This operation makes sure that all data on the x-axis are the same for
    each run and time step.

    Uses [scipy.interpolate.interp1d][].

    Parameters
    ----------
    source : pd.DataFrame
        Input data, contains the columns 'run', 'tstep' and any number of
        ids columns.
    grid : str
        This defines the base ids column that the new base belongs to.
        In other words, this is the `x` column in the interpolation.
    cols : Sequence[str]
        The data in these ids columns will be interpolated.
        In other words, these are the `y` columns in the interpolation.
        IDS columns not defined by grid and cols will be omitted
        from the output.
    grid_base : np.ndarray, optional
        Numpy array with the new base values for the given base column.
        If not defined, use the data in the base column of the first time
        step of the first run as the basis.

    Returns
    -------
    pd.DataFrame
        For the returned dataframe, for each run and time step,
        the values in the base column will be the same.
    """
    if grid_base is None:
        first_run = source.iloc[0].run
        idx = (source[RUN_COL] == first_run) & (source[TSTEP_COL] == 0)
        grid_base = source[idx][grid]
        logger.debug('Rebase ids on %s, using %s from %d to %d with %d steps',
                     first_run, grid, grid_base.min(), grid_base.max(),
                     len(grid_base))

    def refit(gb: pd.DataFrame) -> pd.DataFrame:
        new_values = []

        for value_col in cols:
            f = interp1d(gb[grid],
                         gb[value_col],
                         fill_value='extrapolate',
                         bounds_error=False)
            new_values.append(f(grid_base))

        df = pd.DataFrame((grid_base, *new_values), index=[grid, *cols]).T

        df[TIME_COL] = gb[TIME_COL].iloc[0]
        return df

    grouped = source.groupby([RUN_COL, TSTEP_COL])

    out = grouped.apply(refit).reset_index(
        (RUN_COL, TSTEP_COL)).reset_index(drop=True)

    out = out[[RUN_COL, TSTEP_COL, TIME_COL, grid, *cols]]
    return out


def rebase_on_time(source: pd.DataFrame,
                   *,
                   cols: Sequence[str],
                   time_base: np.ndarray = None) -> pd.DataFrame:
    """Rebase data on new time basis using interpolation.

    This operation makes sure that each run has the same time steps.

    Uses [scipy.interpolate.interp1d][].

    Parameters
    ----------
    source : pd.DataFrame
        Input data, contains the columns 'run', 'tstep' and any number of
        ids columns.
    cols : Sequence[str]
        This defines the columns that should be rebased.
        IDS columns not defined will be omitted from the output.
    time_base : np.ndarray, optional
        Numpy array with the new base values for the time steps.
        If not defined, use the time steps in the first run of the
        source data.

    Returns
    -------
    pd.DataFrame
        For the returned dataframe, for each run the time steps will
        be the same.
    """
    if time_base is None:
        first_run = source.iloc[0].run
        time_base = source[source[RUN_COL] == first_run][TIME_COL].unique()
        logger.debug('Rebase time on %s, from %d to %d with %d steps',
                     first_run, time_base.min(), time_base.max(),
                     len(time_base))

    cols = list(cols)

    n_cols = len(cols)
    n_time_new = len(time_base)

    def refit(gb: pd.DataFrame) -> pd.DataFrame:
        time = gb[TIME_COL].unique()
        values = np.array(gb[cols])

        n_times = len(time)
        n_vals = int(len(values) / n_times)

        values = values.reshape(n_times, n_vals, n_cols).T

        f = interp1d(time,
                     values,
                     fill_value='extrapolate',
                     bounds_error=False)

        values_new = f(time_base)
        values_new = values_new.T.reshape(n_time_new * n_vals, n_cols)

        time_new = np.repeat(time_base, n_vals).reshape(-1, 1)

        tstep_new = np.repeat(np.arange(n_time_new), n_vals).reshape(-1, 1)

        arr = np.hstack((tstep_new, time_new, values_new))

        out = pd.DataFrame(arr, columns=[TSTEP_COL, TIME_COL, *cols])
        out[TSTEP_COL] = out[TSTEP_COL].astype(np.int64)
        return out

    grouped = source.groupby([RUN_COL])

    out = grouped.apply(refit).reset_index(RUN_COL).reset_index(drop=True)
    return out
