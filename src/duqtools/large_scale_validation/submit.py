from __future__ import annotations

import logging
from collections import deque
from pathlib import Path
from typing import Deque, Optional, Sequence

from ..config import load_config
from ..models import Job, Locations
from ..submit import (
    job_array_submitter,
    job_scheduler,
    job_submitter,
    lockfile_ok,
    status_file_ok,
)
from ..utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)
info = logger.info


def submit(*, array: bool, array_script: bool, limit: Optional[int],
           force: bool, max_jobs: int, schedule: bool, max_array_size: int,
           input_file: str, pattern: str, status_filter: Sequence[str],
           **kwargs):
    """Submit nested duqtools configs.

    Parameters
    ----------
    force : bool
        Force the submission even in the presence of lockfiles
    max_jobs : int
        Maximum number of jobs to submit at once
    schedule : bool
        Schedule `max_jobs` to run at once, keeps the process alive until
        finished.
    array : bool
        Submit the jobs as a single array
    array_script : bool
        Create script to submit the jobs as a single array
    max_array_size : int
        Maximum array size for slurm (usually 1001, default = 100)
    limit : Optional[int]
        Limit total number of jobs
    input_file : str
        Only submit jobs for configs where template_data matches a handle in the data.csv
    pattern : str
        Find runs.yaml files only in subdirectories matching this glob pattern
    status_filter : list[str]
        Only submit jobs with this status.
    """
    if pattern is None:
        pattern = '**'

    handles = None
    if input_file:
        handles = read_imas_handles_from_file(input_file).values()

    cwd = Path.cwd()

    dirs = [file.parent for file in cwd.glob(f'{pattern}/runs.yaml')]

    jobs: list[Job] = []

    for drc in dirs:
        config_file = drc / 'duqtools.yaml'
        cfg = load_config(config_file)

        assert cfg.create
        assert cfg.system

        if handles and (cfg.create.template_data not in handles):
            continue

        config_dir = config_file.parent

        jobs.extend(
            Job(run.dirname, cfg=cfg)
            for run in Locations(parent_dir=config_dir, cfg=cfg).runs)

    if not jobs:
        info('No jobs found.')
        return

    job_queue: Deque[Job] = deque()

    for job in jobs:
        status = job.status()

        if status_filter and (status not in status_filter):
            continue
        if not status_file_ok(job, force=force):
            continue
        if not lockfile_ok(job, force=force):
            continue
        job_queue.append(job)

        if len(job_queue) == limit:
            info('Limiting total number of jobs to: %d', len(job_queue))
            break

    if schedule:
        job_scheduler(job_queue, max_jobs=max_jobs)
    elif array or array_script:
        job_array_submitter(job_queue,
                            max_jobs=max_jobs,
                            max_array_size=max_array_size,
                            create_only=array_script,
                            cfg=cfg)
    else:
        job_submitter(job_queue, max_jobs=max_jobs)

    return job_queue
