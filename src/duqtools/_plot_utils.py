import altair as alt
import pandas as pd


def alt_line_chart(source: pd.DataFrame, *, x: str, y: str) -> alt.Chart:
    """Generate an altair line chart from a dataframe.

    The dataframe must be generated using `duqtools.ids.get_ids_dataframe` (or
    have the same format).

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
    slider = alt.binding_range(min=0, max=source['tstep'].max(), step=1)
    select_step = alt.selection_single(name='tstep',
                                       fields=['tstep'],
                                       bind=slider,
                                       init={'tstep': 0})

    chart = alt.Chart(source).mark_line().encode(
        x=f'{x}:Q',
        y=f'{y}:Q',
        color=alt.Color('run:N'),
        tooltip='run',
    ).add_selection(select_step).transform_filter(select_step).interactive()

    return chart


def alt_errorband_chart(source: pd.DataFrame, *, x: str, y: str) -> alt.Chart:
    """Generate an altair errorband plot from a dataframe.

    The dataframe must be generated using `duqtools.ids.get_ids_dataframe` (or
    have the same format).

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
    slider = alt.binding_range(min=0, max=source['tstep'].max(), step=1)
    select_step = alt.selection_single(name='tstep',
                                       fields=['tstep'],
                                       bind=slider,
                                       init={'tstep': 0})

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
