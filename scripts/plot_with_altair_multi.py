import xarray as xr

from duqtools.api import ImasHandle, alt_line_chart

runs = 8000, 8001, 8002

x_var = 'rho_tor_norm'
y_var = 'zeff'

handles = [
    ImasHandle(user='g2vazizi', db='jet', shot='94875', run=run)
    for run in runs
]

ds_list = (handle.get_variables(variables=(x_var, y_var))
           for handle in handles)

idx = xr.DataArray(list(runs), dims=['run'])
dataset = xr.concat(ds_list, idx)

chart = alt_line_chart(dataset, x=x_var, y=y_var)

chart.save('chart.html', scale_factor=2.0)
