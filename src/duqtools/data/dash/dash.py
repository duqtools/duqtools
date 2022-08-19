import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import xarray as xr

from duqtools._plot_utils import alt_errorband_chart, alt_line_chart
from duqtools.api import Variable
from duqtools.ids import (ImasHandle, merge_data, rebase_on_grid,
                          rebase_on_time, standardize_grid)
from duqtools.utils import read_imas_handles_from_file

try:
    default_workdir = sys.argv[1]
except IndexError:
    default_workdir = str(Path.cwd())

PREFIX = 'profiles_1d/$time'
PREFIX0 = 'profiles_1d/0'

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

with st.expander('Click to view runs'):
    st.table(df)


@st.experimental_memo
def get_options(a_run, ids):
    a_profile = ImasHandle(**a_run).get(ids, exclude_empty=True)
    return sorted(a_profile.find_by_group('profiles_1d/0/(.*)').keys())


with st.sidebar:
    ids = st.selectbox('Select IDS', ('core_profiles', ), index=0)

    options = get_options(a_run=df.iloc[0], ids=ids)

    default_x_key = options.index('grid/rho_tor_norm')
    default_y_val = 't_i_average'

    x_key = st.selectbox('Select x', options, index=default_x_key)

    y_keys = st.multiselect('Select y', options, default=default_y_val)

    show_error_bar = st.checkbox(
        'Show errorbar',
        help=(
            'Show standard deviation band around mean y-value. All '
            'y-values are interpolated to put them on a common basis for x.'),
    )

TIME_VAR = dict(
    name='time',
    ids=ids,
    path='time',
    dims=['time'],
)

X_VAR = dict(name=x_key, ids=ids, path=f'{PREFIX}/{x_key}', dims=['x'])

Y_VARS = tuple(
    dict(name=y_key, ids=ids, path=f'{PREFIX}/{y_key}', dims=['x'])
    for y_key in y_keys)


@st.experimental_memo
def _get_dataset(handles, *, time_var, x_var, y_vars):
    datasets = []

    time_var = Variable(**time_var)
    x_var = Variable(**x_var)
    y_vars = tuple((Variable(**y_var) for y_var in y_vars))

    variables = tuple((time_var, x_var, *y_vars))

    for name, handle in handles.items():
        handle = ImasHandle(**handle)

        data_map = handle.get(x_var.ids)

        ds = data_map.to_xarray(variables=variables)

        ds = standardize_grid(
            ds,
            new_dim=x_var.name,
            old_dim=x_var.dims[0],
            new_dim_data=0,
            group=time_var.name,
        )
        datasets.append(ds)

    reference_grid = datasets[0][x_var.name].data

    datasets = [
        rebase_on_grid(ds, coord_dim=x_var.name, new_coords=reference_grid)
        for ds in datasets
    ]

    reference_time = datasets[0][time_var.name].data

    datasets = [
        rebase_on_time(ds, time_dim=time_var.name, new_coords=reference_time)
        for ds in datasets
    ]

    dataset = xr.concat(datasets, 'run')
    dataset['run'] = list(handles.keys())

    return dataset


def get_dataset(handles, *, time_var, x_var, y_vars):
    """Convert to hashable types before calling `_get_dataset`."""
    handles = {name: handle.dict() for name, handle in handles.items()}
    return _get_dataset(handles, time_var=time_var, x_var=x_var, y_vars=y_vars)


source = get_dataset(handles, time_var=TIME_VAR, x_var=X_VAR, y_vars=Y_VARS)

for y_key in y_keys:
    st.header(f'{x_key} vs. {y_key}')

    if show_error_bar:
        chart = alt_errorband_chart(source, x=x_key, y=y_key)
    else:
        chart = alt_line_chart(source, x=x_key, y=y_key)

    st.altair_chart(chart, use_container_width=True)

# with st.form('merge_form'):

#     st.subheader('Merge data')

#     st.write("""
#         With this form you can merge all runs into a new IMAS DB entry.

#         The mean and standard deviation are calculated over all the
#         runs for the fields specified in the side bar.

#         Note that it does not do error propagation yet if the source data have
#         error bars already.
#         """)

#     a_run = df.iloc[0]

#     st.markdown('**Template IMAS entry**')
#     st.write(
#         """This IMAS entry will be used as the template. The template is copied,
#         and any existing data is overwritten for the given fields.""")

#     cols = st.columns((20, 20, 30, 30))

#     template = {
#         'user': cols[0].text_input('User',
#                                    value=a_run.user,
#                                    key='user_template'),
#         'db': cols[1].text_input('Machine', value=a_run.db, key='db_template'),
#         'shot': cols[2].number_input('Shot',
#                                      value=a_run.shot,
#                                      key='shot_template'),
#         'run': cols[3].number_input('Run', value=a_run.run,
#                                     key='run_template'),
#     }

#     template = ImasHandle(**template)

#     st.markdown('**Target IMAS entry**')
#     st.write('The data will be stored in the DB entry given below.')

#     cols = st.columns((20, 20, 30, 30))

#     target = {
#         'user':
#         cols[0].text_input('User',
#                            value=a_run.user,
#                            key='user_target',
#                            disabled=True),
#         'db':
#         cols[1].text_input('Machine', value=a_run.db, key='db_target'),
#         'shot':
#         cols[2].number_input('Shot', value=a_run.shot, key='shot_target'),
#         'run':
#         cols[3].number_input('Run', step=1, key='run_target'),
#     }

#     target = ImasHandle(**target)

#     submitted = st.form_submit_button('Save')

#     if submitted:
#         data = get_data(df, keys=[x_val, *y_vals], PREFIX='profiles_1d')
#         template.copy_data_to(target)
#         merge_data(data=data, target=target, x_val=x_val, y_vals=y_vals)

#         st.success('Success!')
#         st.balloons()
