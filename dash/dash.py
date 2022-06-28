import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from bokeh.plotting import figure

from duqtools.config._runs import Runs

try:
    default_workdir = sys.argv[1]
except IndexError:
    default_workdir = '/afs/eufus.eu/user/g/g2ssmee/jetto_runs/workspace3'

st.title('Plot IDS')
with st.sidebar:
    workdir = st.text_input('Work directory', default_workdir)
    runs_yaml = Path(workdir) / 'runs.yaml'

if not runs_yaml.exists():
    raise ValueError('`runs.yaml` does not exists!')

os.chdir(workdir)

runs = Runs.from_yaml(runs_yaml)

runs_df = pd.DataFrame([run.data_out.dict() for run in runs])

with st.expander('IDS data'):
    st.dataframe(runs_df)

prefix = 'profiles_1d/$i'


def ffmt(s):
    return s.replace(prefix + '/', '')


with st.sidebar:
    profiles = tuple(
        run.data_out.get_ids_tree(exclude_empty=True) for run in runs)

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

    t = st.slider('Time step', max_value=len(time) - 1)

for y_val in y_vals:
    st.header(f'{ffmt(x_val)} vs. {ffmt(y_val)}')

    p = figure(title=f'{ffmt(x_val)} vs {ffmt(y_val)} at t={t}')

    for run in runs:
        d = run.data_out.get_ids_tree()

        # xs = np.arange(len(ys))
        xs = d[x_val.replace('$i', str(t))]

        ys = d[y_val.replace('$i', str(t))]

        p.line(xs, ys, legend_label=str(run.dirname))

    st.bokeh_chart(p)
