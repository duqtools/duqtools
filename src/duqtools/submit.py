import logging
import time
from collections import deque
from itertools import cycle
from pathlib import Path
from typing import Deque, List, Sequence

from ._logging_utils import duqlog_screen
from .config import cfg
from .models import Job, Locations
from .operations import add_to_op_queue, op_queue
from .system import get_system

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


class SubmitError(Exception):
    ...


def Spinner(frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'):
    """Simple spinner animation."""
    yield from cycle(frames)


@add_to_op_queue('Submitting', '{job}')
def _submit_job(job: Job):
    job.submit()


def job_submitter(jobs: Sequence[Job], *, max_jobs):
    for n, job in enumerate(jobs):

        if max_jobs and (n >= max_jobs):
            info(f'Max jobs ({max_jobs}) reached.')
            break

        _submit_job(job)


@add_to_op_queue('Start job scheduler')
def job_scheduler(queue: Deque[Job], max_jobs=10):
    interval = 1.0

    s = Spinner()

    tasks: Deque[Job] = deque()
    completed: Deque[Job] = deque()

    for _ in range(max_jobs):
        job = queue.popleft()
        task = job.start()
        tasks.append(task)

    while tasks:
        time.sleep(interval)
        task = tasks.popleft()
        try:
            next(task)  # Run to the next yield
            tasks.append(task)  # Reschedule
        except StopIteration:
            completed.append(task)

        if queue and len(tasks) < max_jobs:
            job = queue.popleft()
            task = job.start()
            tasks.append(task)

        print(
            f' {next(s)} Running: {len(tasks)},'
            f' queue: {len(queue)}, completed: {len(completed)}',
            end='\033[K\r',
        )


def job_array_submitter(jobs: Sequence[Job], *, max_jobs):
    if len(jobs) == 0:
        duqlog_screen.error('No jobs to submit, not creating array ...')
        return

    for job in jobs:
        op_queue.add(action=lambda: None,
                     description='Adding to array',
                     extra_description=f'{job}')

    get_system().submit_array(jobs)


def submission_script_ok(job):
    submission_script = job.submit_script
    if not submission_script.is_file():
        info('Did not found submission script %s ; Skipping directory...',
             submission_script)
        return False

    return True


def status_file_ok(job, *, force):
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


def lockfile_ok(job, *, force):
    lockfile = job.lockfile
    if lockfile.exists() and not force:
        op_queue.add_no_op(
            description='Not Submitting',
            extra_description=f'{job} (reason: {lockfile} exists)')
        return False

    return True


def get_resubmit_jobs(resubmit_names: Sequence[Path]) -> List[Job]:
    """get_resubmit_jobs.

    Parameters
    ----------
    resubmit_names : Sequence[Path]
        The names (short or full path) of the jobs that need to be resubmitted

    Returns
    -------
    List[Job]
    """
    jobs: List[Job] = []
    run_dict = {run.shortname: run for run in Locations().runs}
    for name in resubmit_names:
        if name in run_dict:  # check for shortname
            jobs.append(Job(run_dict[name].dirname))
        else:
            # It's not a short name, use the argument as the full path to the job
            jobs.append(Job(Path(name)))
    return jobs


def submit(*,
           force: bool,
           max_jobs: int,
           schedule: bool,
           array: bool,
           resubmit: Sequence[Path] = (),
           **kwargs):
    """submit. Function which implements the functionality to submit jobs to
    the cluster.

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
    resubmit : Sequence[Path]
        If any jobs need to be resubmitted, this is has a nonzero length, and
        contains a Sequence of Paths which either are the full Path to the run
        that needs to be resubmitted, or the shortname
    """
    if not cfg.submit:
        raise SubmitError('Submit field required in config file')

    debug('Submit config: %s', cfg.submit)

    if resubmit:
        jobs = get_resubmit_jobs(resubmit)
        force = True
    else:
        jobs = [Job(run.dirname) for run in Locations().runs]

    debug('Case directories: %s', jobs)

    job_queue: Deque[Job] = deque()

    for job in jobs:
        if not status_file_ok(job, force=force):
            continue
        if not lockfile_ok(job, force=force):
            continue
        job_queue.append(job)

    if array and Path('./duqtools_slurm_array.sh').exists() and not force:
        op_queue.add_no_op(
            description='Not Creating Array',
            extra_description='(reason: duqtools_slurm_array.sh exists)')
        op_queue.add_no_op(description='Not Submitting Array',
                           extra_description='use --force to override')
        return

    submitter = job_scheduler if schedule else job_submitter
    submitter = job_array_submitter if array else submitter
    submitter(job_queue, max_jobs=max_jobs)
