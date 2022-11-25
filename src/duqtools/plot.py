from __future__ import annotations

import logging
from pathlib import Path

import click
import xarray as xr

from ._plot_utils import alt_line_chart
from .config import var_lookup
from .ids import ImasHandle
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def plot(*, var_names, imas_paths, user, db, shot, runs, input_files,
         extensions, errorbars, **kwargs):

    handle_lst = []

    for n, imas_path in enumerate(imas_paths):
        handle = ImasHandle.from_string(imas_path)
        handle_lst.append(handle)

    if db and shot and runs:
        for run in runs:
            handle_lst.append(ImasHandle(user=user, db=db, shot=shot, run=run))

    handles = {n: handle for n, handle in enumerate(handle_lst)}

    for input_file in input_files:
        handles.update(read_imas_handles_from_file(input_file))

    if len(handles) == 0:
        raise SystemExit('No data to show.')

    for n, variable in enumerate(var_lookup[var_name]
                                 for var_name in var_names):
        data_var = variable.name
        time_var = variable.dims[0]
        grid_var = variable.dims[1]

        grid_var_norm = var_lookup.normalize(grid_var)

        variables = [data_var, grid_var, time_var]

        if errorbars:
            data_var_std = variable.copy()
            data_var_std.path += '_error_upper'
            data_var_std.name += '_error_upper'

            variables.append(data_var_std)

        datasets = []
        for handle in handles.values():
            ds = handle.get_variables(variables=variables)
            datasets.append(ds)

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

            outfile = Path(f'chart_{n}.{extension}')
            click.secho(f'    file:///{outfile.absolute()}', bold=True)

            chart.save(outfile, scale_factor=2.0)

        click.echo('')
