import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from duqtools._plot_utils import alt_errorband_chart, alt_line_chart
from duqtools.ids import ImasHandle, merge_data, rebase_on_grid, rebase_on_time
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

prefix = 'profiles_1d/$time'


def ffmt(s):
    return s.replace(prefix + '/', '')


def get_options(a_run, ids):
    a_profile = ImasHandle(**a_run).get(ids, exclude_empty=True)
    return sorted(a_profile.find_by_index(f'{prefix}/.*').keys())


with st.sidebar:
    ids = st.selectbox('Select IDS', ('core_profiles', ), index=0)

    options = get_options(a_run=df.iloc[0], ids=ids)

    default_x_key = options.index(f'{prefix}/grid/rho_tor_norm')
    default_y_val = f'{prefix}/t_i_average'

    x_key = st.selectbox('Select x',
                         options,
                         index=default_x_key,
                         format_func=ffmt)

    y_keys = st.multiselect('Select y',
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


rebase_on_grid = st.experimental_memo(rebase_on_grid)
rebase_on_time = st.experimental_memo(rebase_on_time)

y_vals = tuple(ffmt(y_key) for y_key in y_keys)
x_val = ffmt(x_key)

for y_val in y_vals:
    st.header(f'{x_val} vs. {y_val}')

    source = get_data(df, keys=(x_val, y_val), prefix='profiles_1d')

    if show_error_bar:
        source = rebase_on_grid(source, grid=x_val, cols=(y_val, ))
        source = rebase_on_time(source, cols=(x_val, y_val))

        chart = alt_errorband_chart(source, x=x_val, y=y_val)

    else:
        chart = alt_line_chart(source, x=x_val, y=y_val)

    st.altair_chart(chart, use_container_width=True)

with st.form('merge_form'):

    st.subheader('Merge data')

    st.write("""
        With this form you can merge all runs into a new IMAS DB entry.

        The mean and standard deviation are calculated over all the
        runs for the fields specified in the side bar.

        Note that it does not do error propagation yet if the source data have
        error bars already.
        """)

    a_run = df.iloc[0]

    st.markdown('**Template IMAS entry**')
    st.write(
        """This IMAS entry will be used as the template. The template is copied,
        and any existing data is overwritten for the given fields.""")

    cols = st.columns((20, 20, 30, 30))

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

    st.markdown('**Target IMAS entry**')
    st.write('The data will be stored in the DB entry given below.')

    cols = st.columns((20, 20, 30, 30))

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
        data = get_data(df, keys=[x_val, *y_vals], prefix='profiles_1d')
        template.copy_data_to(target)
        merge_data(data=data, target=target, x_val=x_val, y_vals=y_vals)

        st.success('Success!')
        st.balloons()
