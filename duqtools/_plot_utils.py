import altair as alt
import pandas as pd


def alt_line_chart(source: pd.DataFrame, *, x: str, y: str) -> alt.Chart:
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
