from __future__ import annotations

import logging
from pathlib import Path

import click

from ._plot_utils import alt_line_chart
from .ids import ImasHandle, get_ids_dataframe
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def plot(*, x, y, imas_path, input_file, dry_run, **kwargs):
    """Show subroutine to create plots from IDS data."""
    handles = {}

    if imas_path:
        handle = ImasHandle.from_string(imas_path)
        handles[0] = handle

    if input_file:
        handles.update(read_imas_handles_from_file(input_file))

    if len(handles) == 0:
        raise SystemExit('No data to show.')

    source = get_ids_dataframe(handles, keys=(x, y))

    chart = alt_line_chart(source, x=x, y=y)

    outfile = Path('chart.html')

    if not dry_run:
        chart.save(outfile, scale_factor=2.0)

    click.echo('You can now view your plot in your browser:')
    click.echo('')
    click.secho(f'    file:///{outfile.absolute()}', bold=True)
    click.echo('')
