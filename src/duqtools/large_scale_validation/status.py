from pathlib import Path
from typing import List

from ..config import cfg
from ..models import Job, Locations
from ..status import Status, StatusError


def status(*, progress: bool, detailed: bool, **kwargs):
    """Show status of nested runs.

    Parameters
    ----------
    progress : bool
        Show progress bar.
    detailed : bool
        Show detailed progress for every job.
    """

    cwd = Path.cwd()

    config_files = cwd.glob('**/duqtools.yaml')

    jobs: list[Job] = []

    for config_file in config_files:
        cfg.parse_file(config_file)

        if not cfg.status:
            raise StatusError(
                f'Status field required in config file: {config_file}')

        config_dir = config_file.parent

        jobs.extend(Job(run.dirname) for run in Locations(config_dir).runs)

    tracker = Status(jobs)

    if detailed:
        tracker.detailed_status()
    elif progress:
        tracker.progress_status()
    else:
        tracker.simple_status()
