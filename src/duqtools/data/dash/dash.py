from pathlib import Path

import pandas as pd
import streamlit as st
from _shared import (default_workdir, get_dataset, get_ids_options,
                     get_var_options, get_variables)

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
    ids_options = get_ids_options()

    ids = st.selectbox('Select IDS', ids_options, index=0)

    var_options = get_var_options(ids=ids)

    default_x_key = var_options.index('rho_tor_norm')
    default_y_val = 't_i_ave'

    x_key = st.selectbox('Select x', var_options, index=default_x_key)

    y_keys = st.multiselect('Select y', var_options, default=default_y_val)

    st.header('Plotting options')

    show_error_bar = st.checkbox(
        'Show errorbar',
        help=(
            'Show standard deviation band around mean y-value. All '
            'y-values are interpolated to put them on a common basis for x.'),
    )

variables = get_variables(ids=ids, x_key=x_key, y_keys=y_keys)
source = get_dataset(handles, ids=ids, **variables)

for y_key in y_keys:
    st.header(f'{x_key} vs. {y_key}')

    if show_error_bar:
        chart = alt_errorband_chart(source, x=x_key, y=y_key)
    else:
        chart = alt_line_chart(source, x=x_key, y=y_key)

    st.altair_chart(chart, use_container_width=True)
