from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from _shared import add_sidebar_logo, default_workdir, get_dataset

from duqtools._plot_utils import alt_errorband_chart, alt_line_chart
from duqtools.config import var_lookup
from duqtools.utils import read_imas_handles_from_file

add_sidebar_logo()

st.title('Plot IDS')

with st.sidebar:
    st.header('Input data')
    work_dir = st.text_input('Work directory', default_workdir)
    data_file = st.text_input('Data file', 'data.csv')

inp = Path(work_dir) / data_file

if not inp.exists():
    raise ValueError(f'{inp} does not exist!')

handles = read_imas_handles_from_file(inp)
df = pd.DataFrame.from_dict(
    {index: model.model_dump()
     for index, model in handles.items()},
    orient='index')

with st.expander('Click to show runs'):
    st.table(df)

with st.sidebar:
    ids_variables = var_lookup.filter_type('IDS-variable')

    var_names = st.multiselect('Select variable',
                               tuple(ids_variables),
                               default=None)

    st.header('Plotting options')

    aggregate_data = st.checkbox(
        'Aggregate data (mean)',
        help=(
            'Calculate mean y-value and standard deviation. All '
            'y-values are interpolated to put them on a common basis for x.'),
    )
    show_errorbar = st.checkbox(
        'Show error bars',
        help=('Show standard deviation band around mean y-value.'),
    )

    flip_axes = st.checkbox(
        'Flip time/grid axes',
        help=('Flips the time and grid axes.'),
    )

for variable in (var_lookup[var_name] for var_name in var_names):
    source, time_var, grid_var, data_var = get_dataset(
        handles, variable, include_error=show_errorbar)

    st.header(f'{grid_var} vs. {data_var}')

    if flip_axes:
        grid_var, time_var = time_var, grid_var

    if aggregate_data:
        chart = alt_errorband_chart(source, x=grid_var, y=data_var, z=time_var)
    else:
        chart = alt_line_chart(source,
                               x=grid_var,
                               y=data_var,
                               z=time_var,
                               std=show_errorbar)

    st.altair_chart(chart, use_container_width=True)

    if st.button('Save this chart', key=f'download_{grid_var}-{data_var}'):
        fname = f'chart_{grid_var}-{data_var}.html'
        chart.save(fname)
        st.success(f'✔️ Wrote chart to "{fname}"')
