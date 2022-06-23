from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from duqtools.config import cfg
from duqtools.ids import ImasLocation
from duqtools.jetto import JettoSettings

st.title('Plot IDS')

config_path = st.text_input(
    'Path to config',
    '/afs/eufus.eu/user/g/g2ssmee/jetto_runs/workspace/config.yaml')
config_path = Path(config_path)

if not config_path.exists():
    raise ValueError('Config does not exists!')

cfg.read(config_path)


@st.experimental_memo
def load_profile(jset_file):
    jset = JettoSettings.from_file(jset_file)
    imas_loc = ImasLocation.from_jset_output(jset)
    profile = imas_loc.get_ids_tree('core_profiles')
    return profile


jset_files = list(cfg.workspace.cwd.glob('*/*.jset'))

profiles = []
for jset_file in jset_files:
    profile = load_profile(jset_file)
    profiles.append(profile)
    st.write(jset_file)

keys = ('t_i_average', 'zeff')

y_val = st.selectbox('Select IDS', keys, index=0)


@st.experimental_memo
def get_data(y_val):
    plots = []

    for profile in profiles:
        p1d = profile.fields['profiles_1d']
        slices = tuple(p1d[k][y_val] for k in p1d)
        plots.append(slices)

    return plots


data = get_data(y_val)

time_idx = st.slider('Step', min_value=0, max_value=len(data[0]), step=1)

fig, ax = plt.subplots()

for j, y_vals in enumerate(data):

    y = y_vals[time_idx]

    x = np.linspace(0, 1, len(y))

    ax.set_xlabel('x')
    ax.set_ylabel(y_val)

    ax.plot(x, y, label=j)

ax.legend()

st.pyplot(fig)
