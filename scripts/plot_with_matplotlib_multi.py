import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr

from duqtools.api import ImasHandle, standardize_datasets

runs = 8000, 8001, 8002

x_var = 'rho_tor_norm'
y_var = 't_i_ave'
time_var = 'time'

ds_list = []

for run in runs:
    handle = ImasHandle(user='g2vazizi', db='jet', shot='94875', run=run)

    ds = handle.get_variables(variables=(x_var, y_var, time_var))
    ds_list.append(ds)

ds_list = standardize_datasets(ds_list, grid_var=x_var, time_var=time_var)

dataset = xr.concat(ds_list, pd.Index(runs, name='run'))

fig = dataset.plot.scatter(x_var, y_var, hue='time', col='run', marker='.')

plt.show()
