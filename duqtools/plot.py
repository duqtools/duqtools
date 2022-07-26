from __future__ import annotations

import logging
from pathlib import Path

import click

from ._plot_utils import alt_line_chart
from .ids import ImasHandle, get_ids_dataframe
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def plot(*, x_val, y_vals, imas_paths, input_files, dry_run, **kwargs):
    """Show subroutine to create plots from IDS data."""
    handles = {}

    for n, imas_path in enumerate(imas_paths):
        handle = ImasHandle.from_string(imas_path)
        handles[n] = handle

    for input_file in input_files:
        handles.update(read_imas_handles_from_file(input_file))

    if len(handles) == 0:
        raise SystemExit('No data to show.')

    source = get_ids_dataframe(handles, keys=(x_val, *y_vals))

    click.echo('You can now view your plot in your browser:')
    click.echo('')

    for n, y_val in enumerate(y_vals):
        chart = alt_line_chart(source, x=x_val, y=y_val)

        outfile = Path(f'chart_{n}.html')
        click.echo(f'  {x_val} vs. {y_val}:')
        click.secho(f'    file:///{outfile.absolute()}', bold=True)
        click.echo('')

        if not dry_run:
            chart.save(outfile, scale_factor=2.0)
