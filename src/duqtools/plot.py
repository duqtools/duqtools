from __future__ import annotations

import logging
from pathlib import Path

import click
import xarray as xr

from ._plot_utils import alt_line_chart
from .ids import ImasHandle
from .operations import op_queue
from .schema import IDSVariableModel as Variable
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def _path_to_var(path: str, ids: str) -> Variable:
    name = path.split('/*/')[-1]
    return Variable(name=name, path=path, ids=ids, dims=['time', 'x'])


def plot(*, x_path, y_paths, ids, imas_paths, input_files, dry_run, extensions,
         **kwargs):

    handles = {}

    for n, imas_path in enumerate(imas_paths):
        handle = ImasHandle.from_string(imas_path)
        handles[n] = handle

    for input_file in input_files:
        handles.update(read_imas_handles_from_file(input_file))

    if len(handles) == 0:
        raise SystemExit('No data to show.')

    x_var = _path_to_var(x_path, ids)
    y_vars = [_path_to_var(y_path, ids) for y_path in y_paths]
    variables = [x_var] + y_vars

    datasets = []
    for handle in handles.values():
        data_map = handle.get(x_var.ids)
        ds = data_map.to_xarray(variables=variables)
        datasets.append(ds)

    # TODO interpolating?
    dataset = xr.concat(datasets, 'run')

    click.echo('You can now view your plot in your browser:')
    click.echo('')

    for n, y_var in enumerate(y_vars):
        create_chart(n, x_var, y_var, dataset, extensions)


def create_chart(n, x_var, y_var, dataset, extensions):
    chart = alt_line_chart(dataset, x=x_var.name, y=y_var.name)

    click.echo(f'  {x_var} vs. {y_var}:')

    for extension in extensions:

        outfile = Path(f'chart_{n}.{extension}')
        click.secho(f'    file:///{outfile.absolute()}', bold=True)

        op_queue.add(chart.save,
                     args=(outfile, ),
                     kwargs={'scale_factor': 2.0},
                     description='Saving chart',
                     extra_description=f'{outfile}'),

    click.echo('')
