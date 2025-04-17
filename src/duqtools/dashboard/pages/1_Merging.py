from __future__ import annotations

import sys
from getpass import getuser
from pathlib import Path

import pandas as pd
import streamlit as st

from duqtools.config import var_lookup
from duqtools.ids import ImasHandle, merge_data
from duqtools.utils import read_imas_handles_from_file

sys.path.insert(0, str(Path(__file__).parent))

from _shared import get_var_options, add_sidebar_logo  # noqa
from _shared import default_workdir, get_ids_options, get_variables  # noqa

add_sidebar_logo()

st.markdown('# Merge IMAS data')

with st.sidebar:
    st.header('Input data')
    work_dir = st.text_input('Work directory', default_workdir)
    data_file = st.text_input('Data file', 'data.csv')

inp = Path(work_dir) / data_file

if not inp.exists():
    raise ValueError(f'{inp} does not exist!')

handles = read_imas_handles_from_file(inp)
df = pd.DataFrame.from_dict(
    {index: model.model_dump()
     for index, model in handles.items()},
    orient='index')

with st.expander('Click to show runs'):
    st.table(df)

with st.sidebar:
    ids_variables = var_lookup.filter_type('IDS-variable')

    st.header('Merging options')

    merge_all = st.checkbox('Merge all',
                            help='Try to merge all variables.',
                            value=True)

    var_names = st.multiselect('Select variables to merge',
                               tuple(ids_variables),
                               default=None,
                               disabled=merge_all)

if merge_all:
    variables = tuple(ids_variables.values())
else:
    variables = tuple(var_lookup[name] for name in var_names)

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
        'user': cols[0].text_input('User', value=getuser(), key='user_target'),
        'db': cols[1].text_input('Machine', value=a_run.db, key='db_target'),
        'shot': cols[2].number_input('Shot',
                                     value=a_run.shot,
                                     key='shot_target'),
        'run': cols[3].number_input('Run', step=1, key='run_target'),
    }

    target = ImasHandle(**target)

    submitted = st.form_submit_button('Save')

    if submitted:
        template.copy_data_to(target)

        bar = st.progress(0.01)
        merge_data(handles=handles.values(),
                   target=target,
                   variables=variables,
                   callback=bar.progress)
        bar.progress(1.0)

        st.success('Success!')
        st.balloons()
