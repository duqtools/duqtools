import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.interpolate import interp1d

from duqtools.ids import get_ids_tree
from duqtools.ids.handler import ImasHandle
from duqtools.schema.runs import Runs

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

if inp.suffix == '.csv':
    df = pd.read_csv(inp, index_col=0)
elif inp.name == 'runs.yaml':
    runs = Runs.parse_file(inp)
    df = pd.DataFrame([run.data_out.dict() for run in runs])
    df.index = [str(run.dirname) for run in runs]
else:
    raise ValueError(f'Cannot open file: {inp}')

with st.expander('IDS data'):
    st.table(df)

prefix = 'profiles_1d/$i'


def ffmt(s):
    return s.replace(prefix + '/', '')


def get_options(a_run):
    a_profile = get_ids_tree(ImasHandle(**a_run), exclude_empty=True)
    return sorted(a_profile.find_by_index(f'{prefix}/.*').keys())


options = get_options(a_run=df.iloc[0])

with st.sidebar:

    default_x_val = options.index(f'{prefix}/grid/rho_tor_norm')
    default_y_val = f'{prefix}/t_i_average'

    x_val = st.selectbox('Select IDS (x)',
                         options,
                         index=default_x_val,
                         format_func=ffmt)

    y_vals = st.multiselect('Select IDS (y)',
                            options,
                            default=default_y_val,
                            format_func=ffmt)

    show_error_bar = st.checkbox(
        'Show errorbar',
        help=(
            'Show 95\\% confidence interval band around mean y-value. All '
            'y-values are interpolated to put them on a common basis for x.'))


@st.experimental_memo
def get_run_data(row, *, x, y):
    """Get data for single run."""
    profile = get_ids_tree(ImasHandle(**row), exclude_empty=True)
    return profile.to_dataframe(x, y)


@st.experimental_memo
def get_data(df, **kwargs):
    """Get and concatanate data for all runs."""
    runs_data = {
        str(name): get_run_data(row, **kwargs)
        for name, row in df.iterrows()
    }

    return pd.concat(runs_data,
                     names=('run',
                            'index')).reset_index('run').reset_index(drop=True)


@st.experimental_memo
def put_on_common_basis(source):
    n = sum((source['run'] == 'run_0000') & (source['tstep'] == 0))
    mn = source[x].min()
    mx = source[x].max()
    common = np.linspace(mn, mx, n)

    def refit(gb):
        f = interp1d(gb[x],
                     gb[y],
                     fill_value='extrapolate',
                     bounds_error=False)
        new_x = common
        new_y = f(common)
        return pd.DataFrame((new_x, new_y), index=[x, y]).T

    grouped = source.groupby(['run', 'tstep'])
    return grouped.apply(refit).reset_index(
        ('run', 'tstep')).reset_index(drop=True)


for y_val in y_vals:
    x = ffmt(x_val)
    y = ffmt(y_val)

    st.header(f'{x} vs. {y}')

    source = get_data(df, x=x, y=y)

    slider = alt.binding_range(min=0, max=source['tstep'].max(), step=1)
    select_step = alt.selection_single(name='tstep',
                                       fields=['tstep'],
                                       bind=slider,
                                       init={'tstep': 0})

    if show_error_bar:
        source = put_on_common_basis(source)

        line = alt.Chart(source).mark_line().encode(
            x=f'{x}:Q',
            y=f'mean({y}):Q',
            color=alt.Color('tstep:N'),
        ).add_selection(select_step).transform_filter(
            select_step).interactive()

        # altair-viz.github.io/user_guide/generated/core/altair.ErrorBandDef
        band = alt.Chart(source).mark_errorband(
            extent='ci', interpolate='linear').encode(
                x=f'{x}:Q',
                y=f'{y}:Q',
                color=alt.Color('tstep:N'),
            ).add_selection(select_step).transform_filter(
                select_step).interactive()

        chart = line + band

    else:
        chart = alt.Chart(source).mark_line().encode(
            x=f'{x}:Q',
            y=f'{y}:Q',
            color=alt.Color('run:N'),
            tooltip='run',
        ).add_selection(select_step).transform_filter(
            select_step).interactive()

    st.altair_chart(chart, use_container_width=True)
