from pathlib import Path

import pandas as pd
import streamlit as st
from _shared import default_workdir, get_dataset

from duqtools._plot_utils import alt_errorband_chart, alt_line_chart
from duqtools.utils import read_imas_handles_from_file

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
    {index: model.dict()
     for index, model in handles.items()}, orient='index')

with st.expander('Click to show runs'):
    st.table(df)

with st.sidebar:
    from duqtools.config import var_lookup

    ids_variables = var_lookup.filter_type('IDS-variable')

    var_names = st.multiselect('Select variable',
                               tuple(ids_variables),
                               default='t_i_ave')

    st.header('Plotting options')

    show_error_bar = st.checkbox(
        'Show errorbar',
        help=(
            'Show standard deviation band around mean y-value. All '
            'y-values are interpolated to put them on a common basis for x.'),
    )

for variable in (var_lookup[var_name] for var_name in var_names):

    source, time_var, grid_var, data_var = get_dataset(handles, variable)

    st.header(f'{grid_var} vs. {data_var}')

    chart_func = alt_errorband_chart if show_error_bar else alt_line_chart

    if show_error_bar:
        chart = alt_errorband_chart(source, x=grid_var, y=data_var, z=time_var)
    else:
        chart = alt_line_chart(source, x=grid_var, y=data_var, z=time_var)

    st.altair_chart(chart, use_container_width=True)

    if st.button('Save this chart', key=f'download_{grid_var}-{data_var}'):
        fname = f'chart_{grid_var}-{data_var}.html'
        chart.save(fname)
        st.success(f'✔️ Wrote chart to "{fname}"')
