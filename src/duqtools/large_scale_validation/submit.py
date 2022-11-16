from collections import deque
from pathlib import Path
from typing import Deque

from ..config import cfg
from ..models import Job, Locations
from ..submit import (SubmitError, job_scheduler, job_submitter, lockfile_ok,
                      status_file_ok)


def submit(*, force, max_jobs, schedule, **kwargs):
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
    """
    cwd = Path.cwd()

    config_files = cwd.glob('**/duqtools.yaml')

    jobs = []

    for config_file in config_files:
        cfg.parse_file(config_file)

        if not cfg.submit:
            raise SubmitError(
                f'Submit field required in config file: {config_file}')

        config_dir = config_file.parent

        jobs.extend(Job(run.dirname) for run in Locations(config_dir).runs)

    job_queue: Deque[Job] = deque()

    for job in jobs:
        if not status_file_ok(job, force=force):
            continue
        if not lockfile_ok(job, force=force):
            continue
        job_queue.append(job)

    submitter = job_scheduler if schedule else job_submitter

    submitter(job_queue, max_jobs=max_jobs)
