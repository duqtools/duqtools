from typing import Union

import altair as alt
import numpy as np
import pandas as pd
import xarray as xr


def _standardize_data(source: Union[pd.DataFrame, xr.Dataset]) -> pd.DataFrame:
    """Convert Dataset to Dataframe and add required columns for plotting."""
    if isinstance(source, xr.Dataset):
        source = source.to_dataframe().reset_index()

    if 'run' not in source:
        source['run'] = 0

    if 'slider' not in source:
        _, idx = np.unique(source['time'], return_inverse=True)
        source['slider'] = idx

    return source


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
    source = _standardize_data(source)

    max_y = source[y].max()
    max_slider = source['slider'].max()

    slider = alt.binding_range(name='Time index',
                               min=0,
                               max=max_slider,
                               step=1)
    select_step = alt.selection_single(name='time',
                                       fields=['slider'],
                                       bind=slider,
                                       init={'slider': 0})

    chart = alt.Chart(source).mark_line().encode(
        x=f'{x}:Q',
        y=alt.Y(
            f'{y}:Q',
            scale=alt.Scale(domain=(0, max_y)),
            axis=alt.Axis(format='.4~g'),
        ),
        color=alt.Color('run:N'),
        tooltip='run',
    ).add_selection(select_step).transform_filter(select_step).interactive()

    first_run = source.iloc[0].run

    slider = alt.binding_range(name='Reference time index',
                               min=0,
                               max=max_slider,
                               step=1)
    select_step = alt.selection_single(name='reference',
                                       fields=['slider'],
                                       bind=slider,
                                       init={'slider': 0})

    ref = alt.Chart(source).mark_line(strokeDash=[5, 5]).encode(
        x=f'{x}:Q',
        y=f'{y}:Q',
        color=alt.Color('run:N'),
        tooltip='run',
    ).add_selection(select_step).transform_filter(
        select_step).transform_filter(
            alt.datum.run == first_run).interactive()

    return chart + ref


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
    source = _standardize_data(source)

    max_y = source[y].max()
    max_slider = source['slider'].max()

    slider = alt.binding_range(min=0, max=max_slider, step=1)
    select_step = alt.selection_single(name='time',
                                       fields=['slider'],
                                       bind=slider,
                                       init={'slider': 0})

    line = alt.Chart(source).mark_line().encode(
        x=f'{x}:Q',
        y=alt.Y(
            f'mean({y}):Q',
            scale=alt.Scale(domain=(0, max_y)),
            axis=alt.Axis(format='.4~g'),
        ),
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

    slider = alt.binding_range(name='Reference time index',
                               min=0,
                               max=max_slider,
                               step=1)
    select_step = alt.selection_single(name='reference',
                                       fields=['slider'],
                                       bind=slider,
                                       init={'slider': 0})

    ref = alt.Chart(source).mark_line(strokeDash=[5, 5]).encode(
        x=f'{x}:Q',
        y=f'mean({y}):Q',
        color=alt.Color('tstep:N'),
    ).add_selection(select_step).transform_filter(select_step).interactive()

    return line + band + ref
