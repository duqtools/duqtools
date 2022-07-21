import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.interpolate import interp1d

from duqtools.ids import ImasHandle, get_ids_tree
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
    profile = get_ids_tree(ImasHandle(**row), exclude_empty=True)
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
def put_on_common_basis(source, *, x_val, y_vals, common_basis=None):
    if common_basis is None:
        first_run = source.iloc[0].run
        n = sum((source['run'] == first_run) & (source['tstep'] == 0))

        mn = source[x_val].min()
        mx = source[x_val].max()
        common_basis = np.linspace(mn, mx, n)

    def refit(gb):
        new_x = common_basis
        new_ys = []
        for y_val in y_vals:
            f = interp1d(gb[x_val],
                         gb[y_val],
                         fill_value='extrapolate',
                         bounds_error=False)
            new_ys.append(f(common_basis))
        return pd.DataFrame((new_x, *new_ys), index=[x_val, *y_vals]).T

    grouped = source.groupby(['run', 'tstep'])
    return grouped.apply(refit).reset_index(
        ('run', 'tstep')).reset_index(drop=True)


def put_on_common_time(source, *, common_time=None):
    if common_time is None:
        first_run = source.iloc[0].run
        common_time = source[source['run'] == first_run].tstep.unique()

    cols = ['grid/rho_tor_norm', 't_i_average']

    def refit(gb):
        x = gb.tstep.unique()
        y = np.array(gb[cols])

        n_xvals = 100
        n_cols = 2
        n_tstep_old = 2
        n_tstep_new = 5

        # column order = column, xstep, tstep
        y = y.reshape(n_tstep_old, n_xvals, n_cols).T

        f = interp1d(x, y, fill_value='extrapolate', bounds_error=False)

        new_values = f(common_time)
        new_values = new_values.T.reshape(n_tstep_new * n_xvals, n_cols)

        new_time = np.repeat(common_time,
                             n_xvals).reshape(n_tstep_new * n_xvals, 1)

        out = np.hstack((new_time, new_values))

        return pd.DataFrame(out, columns=['tstep', *cols])

    grouped = source.groupby(['run'])

    return grouped.apply(refit).reset_index('run').reset_index(drop=True)


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
        source = put_on_common_basis(source, x_val=x_val, y_vals=[y_val])

        line = alt.Chart(source).mark_line().encode(
            x=f'{x_val}:Q',
            y=f'mean({y_val}):Q',
            color=alt.Color('tstep:N'),
        ).add_selection(select_step).transform_filter(
            select_step).interactive()

        # altair-viz.github.io/user_guide/generated/core/altair.ErrorBandDef
        band = alt.Chart(source).mark_errorband(
            extent='stdev', interpolate='linear').encode(
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

with st.form('Save to new IMAS DB entry'):
    a_run = df.iloc[0]

    st.subheader('Template IMAS entry:')

    cols = st.columns(4)

    template = {
        'user': cols[0].text_input('User',
                                   value=a_run.user,
                                   key='user_template'),
        'db': cols[1].text_input('Machine', value=a_run.db, key='db_template'),
        'shot': cols[2].number_input('Shot',
                                     value=a_run.shot,
                                     key='shot_template'),
        'run': cols[3].number_input('Run', value=a_run.run,
                                    key='run_template'),
    }

    template = ImasHandle(**template)

    st.subheader('Target IMAS entry:')

    cols = st.columns(4)

    target = {
        'user':
        cols[0].text_input('User',
                           value=a_run.user,
                           key='user_target',
                           disabled=True),
        'db':
        cols[1].text_input('Machine', value=a_run.db, key='db_target'),
        'shot':
        cols[2].number_input('Shot', value=a_run.shot, key='shot_target'),
        'run':
        cols[3].number_input('Run', step=1, key='run_target'),
    }

    target = ImasHandle(**target)

    submitted = st.form_submit_button('Save')
    if submitted:
        template_data = get_ids_tree(template)

        # pick first time step as basis
        common_basis = template_data.to_dataframe(x_val,
                                                  time_steps=(0, ))[x_val]

        data = get_data(df, keys=[x_val, *y_vals], prefix='profiles_1d')

        data = put_on_common_basis(data,
                                   x_val=x_val,
                                   y_vals=y_vals,
                                   common_basis=common_basis)

        common_time = [0.0, 0.25, 0.50, 0.75, 1.0]

        # Set to common time basis
        data = put_on_common_time(data, common_time=common_time)

        # template.copy_ids_entry_to(target)

        # core_profiles = target_in.get('core_profiles')
        # ids_mapping = IDSMapping(core_profiles)

        # for y_val in y_keys:
        #     pass

        # with target.open() as data_entry_target:
        #     core_profiles.put(db_entry=data_entry_target)

        # st.success('Success!')
        # st.balloons()
