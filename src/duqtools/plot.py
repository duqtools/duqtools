from __future__ import annotations

import logging
from pathlib import Path

import click
import xarray as xr
from imas2xarray import rebase_all_coords

from ._plot_utils import alt_line_chart
from .config import var_lookup
from .ids import ImasHandle
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def plot(*, var_names, handles, input_files, extensions, errorbars, **kwargs):
    handle_lst = []

    for n, imas_str in enumerate(handles):
        handle = ImasHandle.from_string(imas_str)
        handle_lst.append(handle)

    handles = {n: handle for n, handle in enumerate(handle_lst)}

    for input_file in input_files:
        handles.update(read_imas_handles_from_file(input_file))

    if len(handles) == 0 or len(var_names) == 0:
        raise SystemExit('No data to show.')

    for n, variable in enumerate(var_lookup[var_name]
                                 for var_name in var_names):
        data_var = variable.name
        time_var = variable.dims[0]
        grid_var = variable.dims[1]

        grid_var_norm = var_lookup.normalize(grid_var)

        variables = [data_var, grid_var, time_var]

        if errorbars:
            variables.append(var_lookup.error_upper(data_var))

        datasets = []
        for handle in handles.values():
            ds = handle.get_variables(variables=variables)
            datasets.append(ds)

        datasets = rebase_all_coords(datasets, datasets[0])
        dataset = xr.concat(datasets, 'run')

        chart = alt_line_chart(dataset,
                               x=grid_var_norm,
                               y=data_var,
                               z=time_var,
                               std=errorbars)

        click.echo('You can now view your plot in your browser:')
        click.echo('')

        click.secho(f'  {grid_var_norm} vs. {data_var}:\n', fg='green')

        for extension in extensions:

            outfile = Path(f'chart_{grid_var_norm}-{data_var}.{extension}')
            click.secho(f'    file:///{outfile.absolute()}', bold=True)

            chart.save(outfile, scale_factor=2.0)

        click.echo('')
