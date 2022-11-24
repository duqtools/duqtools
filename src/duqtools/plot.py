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


def plot(*, time_var, grid_var, data_vars, imas_paths, user, db, shot, runs,
         input_files, extensions, errorbars, **kwargs):

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

    grid_ids_var = var_lookup[grid_var]
    data_ids_vars = [var_lookup[y_var] for y_var in data_vars]

    variables = [grid_ids_var] + data_ids_vars
    if errorbars:
        error_ids_vars = [y_var.copy() for y_var in data_ids_vars]
        for y_var in error_ids_vars:
            y_var.path = y_var.path + '_error_upper'
            y_var.name = y_var.name + '_error_upper'
        variables = variables + error_ids_vars

    datasets = []
    for handle in handles.values():
        ds = handle.get_variables(variables=variables)
        datasets.append(ds)

    dataset = xr.concat(datasets, 'run')

    click.echo('You can now view your plot in your browser:')
    click.echo('')

    for n, y_var in enumerate(data_vars):
        click.secho(f'  {grid_var} vs. {y_var}:\n', fg='green')

        chart = alt_line_chart(dataset, x=grid_var, y=y_var, std=errorbars)

        for extension in extensions:

            outfile = Path(f'chart_{n}.{extension}')
            click.secho(f'    file:///{outfile.absolute()}', bold=True)

            chart.save(outfile, scale_factor=2.0)

        click.echo('')
