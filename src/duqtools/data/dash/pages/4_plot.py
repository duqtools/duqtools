import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from duqtools._plot_utils import alt_errorband_chart, alt_line_chart
from duqtools.ids import (ImasHandle, get_ids_tree, rebase_on_ids,
                          rebase_on_time)
from duqtools.ids._io import _get_ids_run_dataframe
from duqtools.utils import read_imas_handles_from_file

try:
    default_workdir = sys.argv[1]
except IndexError:
    default_workdir = str(Path.cwd())

st.title('Plot IDS')

with st.sidebar:
    st.header('Input data')
    work_dir = st.text_input('Work directory', default_workdir)
    data_file = st.text_input('Data file', 'runs.yaml')

inp = Path(work_dir) / data_file

if not inp.exists():
    raise ValueError(f'{inp} does not exist!')

handles = read_imas_handles_from_file(inp)
df = pd.DataFrame.from_dict(
    {index: model.dict()
     for index, model in handles.items()}, orient='index')

with st.expander('Click to view runs'):
    st.table(df)

prefix = 'profiles_1d/$i'


def ffmt(s):
    return s.replace(prefix + '/', '')


def get_options(a_run):
    a_profile = get_ids_tree(ImasHandle(**a_run), exclude_empty=True)
    return sorted(a_profile.find_by_index(f'{prefix}/.*').keys())


options = get_options(a_run=df.iloc[0])

with st.sidebar:

    default_x_key = options.index(f'{prefix}/grid/rho_tor_norm')
    default_y_val = f'{prefix}/t_i_average'

    x_key = st.selectbox('Select IDS (x)',
                         options,
                         index=default_x_key,
                         format_func=ffmt)

    y_keys = st.multiselect('Select IDS (y)',
                            options,
                            default=default_y_val,
                            format_func=ffmt)

    show_error_bar = st.checkbox(
        'Show errorbar',
        help=(
            'Show standard deviation band around mean y-value. All '
            'y-values are interpolated to put them on a common basis for x.'))


@st.experimental_memo()
def get_data(df, **kwargs):
    """Get and concatanate data for all runs."""
    runs_data = {
        str(name): _get_ids_run_dataframe(ImasHandle(**row), **kwargs)
        for name, row in df.iterrows()
    }

    return pd.concat(runs_data,
                     names=('run',
                            'index')).reset_index('run').reset_index(drop=True)


rebase_on_ids = st.experimental_memo(rebase_on_ids)
rebase_on_time = st.experimental_memo(rebase_on_time)

y_vals = tuple(ffmt(y_key) for y_key in y_keys)
x_val = ffmt(x_key)

for y_val in y_vals:
    st.header(f'{x_val} vs. {y_val}')

    source = get_data(df, keys=(x_val, y_val), prefix='profiles_1d')

    if show_error_bar:
        source = rebase_on_ids(source, base_col=x_val, value_cols=[y_val])
        source = rebase_on_time(source, cols=(x_val, y_val))

        chart = alt_errorband_chart(source, x=x_val, y=y_val)

    else:
        chart = alt_line_chart(source, x=x_val, y=y_val)

    st.altair_chart(chart, use_container_width=True)
