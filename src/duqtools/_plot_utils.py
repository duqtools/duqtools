from typing import Union

import altair as alt
import numpy as np
import pandas as pd
import xarray as xr


def alt_line_chart(source: Union[pd.DataFrame, xr.Dataset], *, x: str,
                   y: str) -> alt.Chart:
    """Generate an altair line chart from a dataframe.

    Parameters
    ----------
    source : pd.DataFrame
        Input dataframe
    x : str
        X-value to plot, corresponds to a column in the source data
    y : str
        Y-value to plot, corresponds to a column in the source data

    Returns
    -------
    alt.Chart
        Return an altair chart.
    """
    if isinstance(source, xr.Dataset):
        source = source.to_dataframe().reset_index()

    if 'slider' not in source:
        _, idx = np.unique(source['time'], return_inverse=True)
        source['slider'] = idx

    slider = alt.binding_range(min=0, max=source['slider'].max(), step=1)
    select_step = alt.selection_single(name='time',
                                       fields=['slider'],
                                       bind=slider,
                                       init={'slider': 0})

    chart = alt.Chart(source).mark_line().encode(
        x=f'{x}:Q',
        y=f'{y}:Q',
        color=alt.Color('run:N'),
        tooltip='run',
    ).add_selection(select_step).transform_filter(select_step).interactive()

    return chart


def alt_errorband_chart(source: Union[pd.DataFrame, xr.Dataset], *, x: str,
                        y: str) -> alt.Chart:
    """Generate an altair errorband plot from a dataframe.

    Parameters
    ----------
    source : pd.DataFrame
        Input dataframe
    x : str
        X-value to plot, corresponds to a column in the source data
    y : str
        Y-value to plot, corresponds to a column in the source data

    Returns
    -------
    alt.Chart
        Return an altair chart.
    """
    if isinstance(source, xr.Dataset):
        source = source.to_dataframe().reset_index()

    if 'slider' not in source:
        _, idx = np.unique(source['time'], return_inverse=True)
        source['slider'] = idx

    slider = alt.binding_range(min=0, max=source['slider'].max(), step=1)
    select_step = alt.selection_single(name='time',
                                       fields=['slider'],
                                       bind=slider,
                                       init={'slider': 0})

    line = alt.Chart(source).mark_line().encode(
        x=f'{x}:Q',
        y=f'mean({y}):Q',
        color=alt.Color('tstep:N'),
    ).add_selection(select_step).transform_filter(select_step).interactive()

    # altair-viz.github.io/user_guide/generated/core/altair.ErrorBandDef
    band = alt.Chart(source).mark_errorband(
        extent='stdev', interpolate='linear').encode(
            x=f'{x}:Q',
            y=f'{y}:Q',
            color=alt.Color('tstep:N'),
        ).add_selection(select_step).transform_filter(
            select_step).interactive()

    chart = line + band

    return chart
