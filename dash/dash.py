import os
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from duqtools.config._runs import Runs

try:
    default_workdir = sys.argv[1]
except IndexError:
    default_workdir = '/afs/eufus.eu/user/g/g2ssmee/jetto_runs/workspace3'

st.title('Plot IDS')

with st.sidebar:
    st.header('Input data')
    workdir = st.text_input('Work directory', default_workdir)
    runs_yaml = Path(workdir) / 'runs.yaml'

if not runs_yaml.exists():
    raise ValueError('`runs.yaml` does not exists!')

os.chdir(workdir)

runs = Runs.parse_file(runs_yaml)

runs_df = pd.DataFrame([run.data_out.dict() for run in runs])

with st.expander('IDS data'):
    st.dataframe(runs_df)

prefix = 'profiles_1d/$i'


def ffmt(s):
    return s.replace(prefix + '/', '')


# @st.cache
def load_ids_data(runs):
    return tuple(run.data_out.get_ids_tree(exclude_empty=True) for run in runs)


profiles = load_ids_data(runs)

with st.sidebar:

    options = sorted(profiles[0].find_by_index(f'{prefix}/.*').keys())

    time = profiles[0]['time']

    default_x_val = options.index(f'{prefix}/grid/rho_tor')
    default_y_val = f'{prefix}/t_i_average'

    x_val = st.selectbox('Select IDS (x)',
                         options,
                         index=default_x_val,
                         format_func=ffmt)
    y_vals = st.multiselect('Select IDS (y)',
                            options,
                            default=default_y_val,
                            format_func=ffmt)

for y_val in y_vals:
    st.header(f'{ffmt(x_val)} vs. {ffmt(y_val)}')

    key = f'profiles_1d/(\\d+)/({ffmt(x_val)}|{ffmt(y_val)})'

    d = {}

    for run, profile in zip(runs, profiles):
        ret = profile.find_by_group(key)
        df = pd.DataFrame(ret)
        df.columns = df.columns.set_names(('time_step', 'key'))
        df = df.T.unstack('time_step').T
        df = df.reset_index('time_step')  # .reset_index(drop=True)
        d[run.dirname] = df

    df = pd.concat(d,
                   names=('run',
                          'index')).reset_index('run').reset_index(drop=True)

    df['run'] = df['run'].apply(str)
    df['time_step'] = df['time_step'].apply(int)

    x = ffmt(x_val)
    y = ffmt(y_val)

    source = df

    slider = alt.binding_range(min=0, max=source['time_step'].max(), step=1)
    select_step = alt.selection_single(name='time_step',
                                       fields=['time_step'],
                                       bind=slider,
                                       init={'time_step': 0})

    chart = alt.Chart(source).mark_line().encode(
        x=f'{x}:Q',
        y=f'{y}:Q',
        color=alt.Color('run:N'),
        tooltip='run',
    ).add_selection(select_step).transform_filter(select_step).interactive()

    st.altair_chart(chart, use_container_width=True)
