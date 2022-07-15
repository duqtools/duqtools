import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.interpolate import interp1d

from duqtools.config import Runs
from duqtools.config.imaslocation import ImasLocation
from duqtools.ids import get_ids_tree

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
    a_profile = get_ids_tree(ImasLocation(**a_run), exclude_empty=True)
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
            'Show 95\\% confidence interval band around mean y-value. All '
            'y-values are interpolated to put them on a common basis for x.'))


@st.experimental_memo
def get_run_data(row, *, keys, **kwargs):
    """Get data for single run."""
    profile = get_ids_tree(ImasLocation(**row), exclude_empty=True)
    return profile.to_dataframe(*keys, **kwargs)


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
def put_on_common_basis(source, *, x, y, common_basis=None):
    if common_basis is None:
        n = sum((source['run'] == 'run_0000') & (source['tstep'] == 0))
        mn = source[x].min()
        mx = source[x].max()
        common_basis = np.linspace(mn, mx, n)

    def refit(gb):
        f = interp1d(gb[x],
                     gb[y],
                     fill_value='extrapolate',
                     bounds_error=False)
        new_x = common_basis
        new_y = f(common_basis)
        return pd.DataFrame((new_x, new_y), index=[x, y]).T

    grouped = source.groupby(['run', 'tstep'])
    return grouped.apply(refit).reset_index(
        ('run', 'tstep')).reset_index(drop=True)


y_vals = tuple(ffmt(y_key) for y_key in y_keys)
x_val = ffmt(x_key)

for y_val in y_vals:
    st.header(f'{x_val} vs. {y_val}')

    source = get_data(df, keys=(x_val, y_val), prefix='profiles_1d')

    slider = alt.binding_range(min=0, max=source['tstep'].max(), step=1)
    select_step = alt.selection_single(name='tstep',
                                       fields=['tstep'],
                                       bind=slider,
                                       init={'tstep': 0})

    if show_error_bar:
        source = put_on_common_basis(source, x=x_val, y=y_val)

        line = alt.Chart(source).mark_line().encode(
            x=f'{x_val}:Q',
            y=f'mean({y_val}):Q',
            color=alt.Color('tstep:N'),
        ).add_selection(select_step).transform_filter(
            select_step).interactive()

        # altair-viz.github.io/user_guide/generated/core/altair.ErrorBandDef
        band = alt.Chart(source).mark_errorband(
            extent='ci', interpolate='linear').encode(
                x=f'{x_val}:Q',
                y=f'{y_val}:Q',
                color=alt.Color('tstep:N'),
            ).add_selection(select_step).transform_filter(
                select_step).interactive()

        chart = line + band

    else:
        chart = alt.Chart(source).mark_line().encode(
            x=f'{x_val}:Q',
            y=f'{y_val}:Q',
            color=alt.Color('run:N'),
            tooltip='run',
        ).add_selection(select_step).transform_filter(
            select_step).interactive()

    st.altair_chart(chart, use_container_width=True)
