from __future__ import annotations

import logging
from pathlib import Path

import click

from ._plot_utils import alt_line_chart
from .ids import ImasHandle, get_ids_dataframe
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def plot(*, x, y, user, db, shot, run, inp, **kwargs):
    """Show subroutine to create plots from datas."""
    handles = []

    if user and db and shot and run:
        handle = ImasHandle(
            user=user,
            db=db,
            shot=shot,
            run=run,
        )
        handles.append(handle)

    if inp:
        handles = read_imas_handles_from_file(inp)

    if len(handles) == 0:
        raise SystemExit('No data to show.')

    source = get_ids_dataframe(handles, keys=(x, y))

    chart = alt_line_chart(source, x=x, y=y)

    outfile = Path('chart.html')

    chart.save(outfile, scale_factor=2.0)

    click.echo('You can now view your plot in your browser:')
    click.echo('')
    click.secho(f'    file:///{outfile.absolute()}', bold=True)
    click.echo('')
