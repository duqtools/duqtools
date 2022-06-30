import itertools
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from bokeh.layouts import column
from bokeh.models import CustomJS, Slider
from bokeh.palettes import Plasma as palette
from bokeh.plotting import ColumnDataSource, figure

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

runs = Runs.from_yaml(runs_yaml)

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


@st.cache
def get_data_sources(profiles, *, x_val: str, y_val: str):
    data_sets = []

    for profile in profiles:
        data = {}
        for k, v in profile.find_by_index(x_val)[x_val].items():
            data[f'x{k}'] = v
        for k, v in profile.find_by_index(y_val)[y_val].items():
            data[f'y{k}'] = v
        data_sets.append(data)

    return data_sets


n_time_steps = len(profiles[0]['time'])

for y_val in y_vals:
    st.header(f'{ffmt(x_val)} vs. {ffmt(y_val)}')

    data_sets = get_data_sources(profiles, x_val=x_val, y_val=y_val)
    sources = tuple(ColumnDataSource(data=data) for data in data_sets)

    plot = figure(title=f'{ffmt(x_val)} vs {ffmt(y_val)}')

    time_slider = Slider(start=0,
                         end=n_time_steps - 1,
                         value=0,
                         step=1,
                         title='Time step')

    colors = itertools.cycle(palette.get(len(sources), palette[11]))

    for i, source in enumerate(sources):
        color = next(colors)

        line = plot.line(x='x0',
                         y='y0',
                         source=source,
                         color=color,
                         line_width=3,
                         line_alpha=0.6,
                         legend_label=str(runs[i].dirname))

        callback = CustomJS(args=dict(source=source,
                                      time_step=time_slider,
                                      line=line),
                            code="""

            const T = time_step.value;
            var x_column = 'x' + T;
            var y_column = 'y' + T;

            line.glyph.x.field = x_column;
            line.glyph.y.field = y_column;

            source.change.emit();
        """)

        time_slider.js_on_change('value', callback)

    layout = column(
        plot,
        column(time_slider),
    )

    st.bokeh_chart(layout)
