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
    {
        index: model.model_dump()
        for index, model in handles.items()
    },
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

    axes_opts = 'grid', 'data', 'time'
    x_axis = st.selectbox('X axis', axes_opts, index=0)
    y_axis = st.selectbox('Y axis', axes_opts, index=1)
    z_axis = st.selectbox('Z axis', axes_opts, index=2)

for variable in (var_lookup[var_name] for var_name in var_names):
    source, time_var, grid_var, data_var = get_dataset(
        handles, variable, include_error=show_errorbar)

    st.header(f'{grid_var} vs. {data_var}')

    axes = {'time': time_var, 'grid': grid_var, 'data': data_var}
    x_var = axes[x_axis]
    y_var = axes[y_axis]
    z_var = axes[z_axis]

    if aggregate_data:
        chart = alt_errorband_chart(source, x=x_var, y=y_var, z=z_var)
    else:
        chart = alt_line_chart(source,
                               x=x_var,
                               y=y_var,
                               z=z_var,
                               std=show_errorbar)

    st.altair_chart(chart, use_container_width=True)

    if st.button('Save this chart', key=f'download_{x_var}-{y_var}'):
        fname = f'chart_{x_var}-{y_var}.html'
        chart.save(fname)
        st.success(f'✔️ Wrote chart to "{fname}"')
