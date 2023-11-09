from __future__ import annotations

from typing import TYPE_CHECKING, Union

import altair as alt
import numpy as np
import xarray as xr

if TYPE_CHECKING:
    import pandas as pd


def _standardize_data(source: Union[pd.DataFrame, xr.Dataset],
                      z: str = 'time') -> pd.DataFrame:
    """Convert Dataset to Dataframe and add required columns for plotting."""
    if isinstance(source, xr.Dataset):
        source = source.to_dataframe().reset_index()

    if 'run' not in source:
        source['run'] = 0

    if 'slider' not in source:
        _, idx = np.unique(source[z], return_inverse=True)
        source['slider'] = idx

    return source


def alt_line_chart(source: Union[pd.DataFrame, xr.Dataset],
                   *,
                   x: str,
                   y: str,
                   z: str = 'time',
                   std: bool = False) -> alt.Chart:
    """Generate an altair line chart from a dataframe.

    Parameters
    ----------
    source : pd.DataFrame
        Input dataframe
    x : str
        X-value to plot, corresponds to a column in the source data
    y : str
        Y-value to plot, corresponds to a column in the source data
    z : str
        Slider variable (time), corresponds to a column in the source data

    std : bool
        Plot the error bound from {x}_error_upper in the plot as well

    Returns
    -------
    alt.Chart
        Return an altair chart.
    """
    source = _standardize_data(source, z=z)
    max_y = source[y].max()

    if std:
        source[y + '_upper'] = source[y] + source[y + '_error_upper']
        source[y + '_lower'] = source[y] - source[y + '_error_upper']
        max_y = source[y + '_upper'].max()

    max_slider = source['slider'].max()

    if std:
        band = alt.Chart(source).mark_area(opacity=0.3).encode(
            x=f'{x}:Q',
            y=alt.Y(f'{y}_upper:Q', title=y),
            y2=alt.Y2(f'{y}_lower:Q', title=y),
            color=alt.Color('run:N'),
        )

    line = alt.Chart(source).mark_line().encode(
        x=f'{x}:Q',
        y=alt.Y(
            f'{y}:Q',
            scale=alt.Scale(domain=(0, max_y)),
            axis=alt.Axis(format='.4~g'),
        ),
        color=alt.Color('run:N'),
        tooltip='run',
    )

    ref = alt.Chart(source).mark_line(strokeDash=[5, 5]).encode(
        x=f'{x}:Q', y=f'{y}:Q', color=alt.Color('run:N'), tooltip='run')

    if max_slider != 0:
        slider = alt.binding_range(name=f'{z} index',
                                   min=0,
                                   max=max_slider,
                                   step=1)
        select_step = alt.selection_point(name=z,
                                          fields=['slider'],
                                          bind=slider,
                                          value=0)
        line = line.add_params(select_step).transform_filter(
            select_step).interactive()
        if std:
            band = band.transform_filter(select_step).interactive()

        first_run = source.iloc[0].run
        slider = alt.binding_range(name=f'Reference {z} index',
                                   min=0,
                                   max=max_slider,
                                   step=1)
        select_step = alt.selection_point(name='reference',
                                          fields=['slider'],
                                          bind=slider,
                                          value=0)

        ref = ref.add_params(select_step).transform_filter(
            select_step).transform_filter(
                alt.datum.run == first_run).interactive()

    if std:
        return line + ref + band
    else:
        return line + ref


def alt_errorband_chart(source: Union[pd.DataFrame, xr.Dataset],
                        *,
                        x: str,
                        y: str,
                        z: str = 'time') -> alt.Chart:
    """Generate an altair errorband plot from a dataframe.

    Parameters
    ----------
    source : pd.DataFrame
        Input dataframe
    x : str
        X-value to plot, corresponds to a column in the source data
    y : str
        Y-value to plot, corresponds to a column in the source data
    z : str
        Slider variable (time), corresponds to a column in the source data

    Returns
    -------
    alt.Chart
        Return an altair chart.
    """
    source = _standardize_data(source, z=z)

    max_y = source[y].max()
    max_slider = source['slider'].max()

    line = alt.Chart(source).mark_line().encode(
        x=f'{x}:Q',
        y=alt.Y(
            f'mean({y}):Q',
            scale=alt.Scale(domain=(0, max_y)),
            axis=alt.Axis(format='.4~g'),
        ),
        color=alt.Color('tstep:N'),
    )

    # altair-viz.github.io/user_guide/generated/core/altair.ErrorBandDef
    band = alt.Chart(source).mark_errorband(extent='stdev',
                                            interpolate='linear').encode(
                                                x=f'{x}:Q',
                                                y=f'{y}:Q',
                                                color=alt.Color('tstep:N'),
                                            )

    ref = alt.Chart(source).mark_line(strokeDash=[5, 5]).encode(
        x=f'{x}:Q',
        y=f'mean({y}):Q',
        color=alt.Color('tstep:N'),
    )

    if max_slider != 0:
        slider = alt.binding_range(min=0, max=max_slider, step=1)
        select_step = alt.selection_point(name=z,
                                          fields=['slider'],
                                          bind=slider,
                                          value=0)

        line = line.add_params(select_step).transform_filter(
            select_step).interactive()
        band = band.add_params(select_step).transform_filter(
            select_step).interactive()

        slider = alt.binding_range(name=f'Reference {z} index',
                                   min=0,
                                   max=max_slider,
                                   step=1)

        select_step = alt.selection_point(name='reference',
                                          fields=['slider'],
                                          bind=slider,
                                          value=0)

        ref = ref.add_params(select_step).transform_filter(
            select_step).interactive()

    return line + band + ref
