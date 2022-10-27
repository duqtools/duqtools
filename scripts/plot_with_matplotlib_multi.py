import pandas as pd
import xarray as xr

from duqtools.api import ImasHandle

runs = 8000, 8001, 8002

x_var = 'rho_tor_norm'
y_var = 't_i_ave'

ds_list = []

for run in runs:
    handle = ImasHandle(user='g2vazizi', db='jet', shot='94875', run=run)

    ds = handle.get_variables(variables=(x_var, y_var))
    ds_list.append(ds)

dataset = xr.concat(ds_list, pd.Index(runs, name='run'))

# MPL stuff
