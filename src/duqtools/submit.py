from __future__ import annotations

import logging
import time
from collections import deque
from itertools import cycle
from pathlib import Path
from typing import Deque, Optional, Sequence

from ._logging_utils import duqlog_screen
from .config import Config
from .create import CreateError
from .models import Job, Locations
from .operations import add_to_op_queue, op_queue
from .systems import get_system

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


class SubmitError(Exception):
    ...


def Spinner(frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'):
    """Simple spinner animation."""
    yield from cycle(frames)


@add_to_op_queue('Submitting', '{job}')
def _submit_job(job: Job, *, delay: float = 0):
    """
    Parameters
    ----------
    delay : float
        Add a delay to avoid all jobs starting at the same time.
        This causes issues with slurm, for example.
    """
    if delay:
        time.sleep(delay)
    job.submit()


def job_submitter(jobs: Sequence[Job], *, max_jobs: int, **kwargs):
    for n, job in enumerate(jobs):
        if max_jobs and (n >= max_jobs):
            info(f'Max jobs ({max_jobs}) reached.')
            break

        _submit_job(job, delay=0.1)


@add_to_op_queue('Start job scheduler')
def job_scheduler(queue: Deque[Job], *, max_jobs: int = 10, **kwargs):
    interval = 1.0

    s = Spinner()

    tasks: Deque[Job] = deque()
    completed: Deque[Job] = deque()

    while tasks or queue:
        while queue and len(tasks) < max_jobs:
            job = queue.popleft()
            task = job.start()
            tasks.append(task)
            # starting jobs at the same time causes issues
            time.sleep(0.1)

        time.sleep(interval)
        task = tasks.popleft()
        try:
            next(task)  # Run to the next yield
            tasks.append(task)  # Reschedule
        except StopIteration:
            completed.append(task)

        print(
            f' {next(s)} Running: {len(tasks)},'
            f' queue: {len(queue)}, completed: {len(completed)}',
            end='\033[K\r',
        )


def job_array_submitter(
    jobs: Sequence[Job],
    *,
    max_jobs: int = 10,
    max_array_size: int = 100,
    create_only: bool = False,
    cfg: Config,
):
    if len(jobs) == 0:
        duqlog_screen.error('No jobs to submit, not creating array ...')
        return

    for job in jobs:
        op_queue.add(action=lambda: None,
                     description='Adding to array',
                     extra_description=f'{job}')

    if not cfg.create:
        raise CreateError('Create field required in config file')

    system = get_system(cfg=cfg)

    system.submit_array(jobs,
                        max_jobs=max_jobs,
                        max_array_size=max_array_size,
                        create_only=create_only)


def submission_script_ok(job) -> bool:
    submission_script = job.submit_script
    if not submission_script.is_file():
        info('Did not found submission script %s ; Skipping directory...',
             submission_script)
        return False

    return True


def status_file_ok(job, *, force: bool) -> bool:
    status_file = job.status_file
    if job.has_status and not force:
        if not status_file.is_file():
            logger.warning('Status file %s is not a file', status_file)
        with open(status_file) as f:
            info('Status of %s: %s. To rerun enable the --force flag',
                 status_file, f.read())
        op_queue.add_no_op(
            description='Not Submitting',
            extra_description=f'{job} (reason: status file exists)')
        return False

    return True


def lockfile_ok(job: Job, *, force: bool) -> bool:
    lockfile = job.lockfile
    if lockfile.exists() and not force:
        op_queue.add_no_op(
            description='Not Submitting',
            extra_description=f'{job} (reason: {lockfile} exists)')
        return False

    return True


def get_resubmit_jobs(cfg: Config, *, resubmit_names: Sequence[Path],
                      locations: Locations) -> list[Job]:
    """Get list of jobs to resubmit.

    Parameters
    ----------
    cfg: Config
        Duqtools config.
    resubmit_names : Sequence[Path]
        The names (short or full path) of the jobs that need to be resubmitted
    locations : Locations
        Instance of Locations, use these to search for jobs

    Returns
    -------
    list[Job]
    """
    jobs: list[Job] = []
    run_dict = {run.shortname: run for run in locations.runs}
    for name in resubmit_names:
        if name in run_dict:  # check for shortname
            name = run_dict[name].dirname
        else:
            # It's not a short name, use the argument as the full path to the job
            name = Path(name)

        jobs.append(Job(name, cfg=cfg))
    return jobs


def submit(*,
           cfg: Config,
           force: bool = False,
           max_jobs: int = 10,
           max_array_size: int = 100,
           schedule: bool = False,
           array: bool = False,
           array_script: bool = False,
           limit: Optional[int] = None,
           resubmit: Sequence[Path] = (),
           status_filter: Sequence[str] = (),
           parent_dir: Optional[Path] = None,
           **kwargs):
    """Submit jobs to the cluster.

    Parameters
    ----------
    force : bool
        Force the submission even in the presence of lockfiles
    max_jobs : int
        Maximum number of jobs to submit at once
    max_array_size : int
        Maximum array size for slurm (usually 1001, default = 100)
    schedule : bool
        Schedule `max_jobs` to run at once, keeps the process alive until
        finished.
    array : bool
        Submit the jobs as a single array
    array_script : bool
        Create script to submit the jobs as a single array
    limit : Optional[int]
        Limit total number of jobs
    resubmit : Sequence[Path]
        If any jobs need to be resubmitted, this is has a nonzero length, and
        contains a Sequence of Paths which either are the full Path to the run
        that needs to be resubmitted, or the shortname
    status_filter : list[str]
        Only submit jobs with this status.
    parent_dir : Path
        Search for jobs in this directory.
    """

    locations = Locations(parent_dir=parent_dir, cfg=cfg)

    if resubmit:
        jobs = get_resubmit_jobs(cfg=cfg,
                                 resubmit_names=resubmit,
                                 locations=locations)
        force = True
    else:
        jobs = [Job(run.dirname, cfg=cfg) for run in locations.runs]

    debug('Case directories: %s', jobs)

    job_queue: Deque[Job] = deque()

    if array and Path('./duqtools_slurm_array.sh').exists() and not force:
        op_queue.add_no_op(
            description='Not Creating Array',
            extra_description='(reason: duqtools_slurm_array.sh exists)')
        op_queue.add_no_op(description='Not Submitting Array',
                           extra_description='use --force to override')
        return job_queue

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


def submit_api(config: dict, **kwargs):
    """Wrapper around submit for python api."""
    cfg = Config.from_dict(config)
    return submit(cfg=cfg, **kwargs)
