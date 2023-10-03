from __future__ import annotations

from pathlib import Path

import click

from ..config import load_config
from ..models import Job, Locations
from ..status import Status, StatusError


def status(*, progress: bool, detailed: bool, pattern: str, **kwargs):
    """Show status of nested runs.

    Parameters
    ----------
    progress : bool
        Show progress bar.
    detailed : bool
        Show detailed progress for every job.
    pattern : str
        Show status only for subdirectories matching this glob pattern
    """
    if pattern is None:
        pattern = '**'

    cwd = Path.cwd()

    config_files = cwd.glob(f'{pattern}/duqtools.yaml')

    all_jobs: list[Job] = []

    click.echo(Job.status_symbol_help())
    click.echo()

    for config_file in config_files:
        cfg = load_config(config_file)

        if not cfg.system:
            raise StatusError(
                f'Status field required in config file: {config_file}')

        config_dir = config_file.parent

        jobs = [
            Job(run.dirname, cfg=cfg)
            for run in Locations(parent_dir=config_dir, cfg=cfg).runs
        ]
        all_jobs.extend(jobs)

        dirname = config_file.parent.relative_to(cwd)
        tag = cfg.tag
        status = ''.join(job.status_symbol for job in jobs)

        click.echo(f'{dirname} ({tag}): {status}')

    click.echo()

    tracker = Status(all_jobs)

    if detailed:
        tracker.detailed_status()
    elif progress:
        tracker.progress_status()
    else:
        tracker.simple_status()
