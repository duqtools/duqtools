import logging
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from ._constants import RUN_COL, TIME_COL, TSTEP_COL

logger = logging.getLogger(__name__)


def rebase_on_ids(source: pd.DataFrame,
                  *,
                  base_col: str,
                  value_cols: Sequence[str],
                  new_base: np.ndarray = None) -> pd.DataFrame:
    """Rebase data on new ids basis using interpolation.

    This operation makes sure that all data on the x-axis are the same for
    each run and time step.

    Uses [scipy.interpolate.interp1d][].

    Parameters
    ----------
    source : pd.DataFrame
        Input data, contains the columns 'run', 'tstep' and any number of
        ids columns.
    base_col : str
        This defines the base ids column that the new base belongs to.
        In other words, this is the `x` column in the interpolation.
    value_cols : Sequence[str]
        The data in these ids columns will be interpolated.
        In other words, these are the `y` columns in the interpolation.
        IDS columns not defined by base_col and value_cols will be omitted
        from the output.
    new_base : np.ndarray, optional
        Numpy array with the new base values for the given base column.
        If not defined, use the data in the base column of the first time
        step of the first run as the basis.

    Returns
    -------
    pd.DataFrame
        For the returned dataframe, for each run and time step,
        the values in the base column will be the same.
    """
    if new_base is None:
        first_run = source.iloc[0].run
        idx = (source[RUN_COL] == first_run) & (source[TSTEP_COL] == 0)
        new_base = source[idx][base_col]
        logger.debug('Rebase ids on %s, using %s from %d to %d with %d steps',
                     first_run, base_col, new_base.min(), new_base.max(),
                     len(new_base))

    def refit(gb: pd.DataFrame) -> pd.DataFrame:
        new_values = []

        for value_col in value_cols:
            f = interp1d(gb[base_col],
                         gb[value_col],
                         fill_value='extrapolate',
                         bounds_error=False)
            new_values.append(f(new_base))

        df = pd.DataFrame((new_base, *new_values),
                          index=[base_col, *value_cols]).T

        df[TIME_COL] = gb[TIME_COL].iloc[0]
        return df

    grouped = source.groupby([RUN_COL, TSTEP_COL])

    out = grouped.apply(refit).reset_index(
        (RUN_COL, TSTEP_COL)).reset_index(drop=True)

    out = out[[RUN_COL, TSTEP_COL, TIME_COL, base_col, *value_cols]]
    return out


def rebase_on_time(source: pd.DataFrame,
                   *,
                   cols: Sequence[str],
                   new_base: np.ndarray = None) -> pd.DataFrame:
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
    new_base : np.ndarray, optional
        Numpy array with the new base values for the time steps.
        If not defined, use the time steps in the first run of the
        source data.

    Returns
    -------
    pd.DataFrame
        For the returned dataframe, for each run the time steps will
        be the same.
    """
    if new_base is None:
        first_run = source.iloc[0].run
        new_base = source[source[RUN_COL] == first_run][TIME_COL].unique()
        logger.debug('Rebase time on %s, from %d to %d with %d steps',
                     first_run, new_base.min(), new_base.max(), len(new_base))

    cols = list(cols)

    n_cols = len(cols)
    n_time_new = len(new_base)

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

        values_new = f(new_base)
        values_new = values_new.T.reshape(n_time_new * n_vals, n_cols)

        time_new = np.repeat(new_base, n_vals).reshape(-1, 1)

        tstep_new = np.repeat(np.arange(n_time_new), n_vals).reshape(-1, 1)

        arr = np.hstack((tstep_new, time_new, values_new))

        out = pd.DataFrame(arr, columns=[TSTEP_COL, TIME_COL, *cols])
        out[TSTEP_COL] = out[TSTEP_COL].astype(np.int64)
        return out

    grouped = source.groupby([RUN_COL])

    out = grouped.apply(refit).reset_index(RUN_COL).reset_index(drop=True)
    return out
