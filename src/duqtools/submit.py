import logging
import queue
import subprocess
from collections import deque
from typing import Any, List

import click

from ._job import Job
from .config import cfg
from .models import WorkDirectory
from .operations import add_to_op_queue, op_queue

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


@add_to_op_queue('Submitting', '{job}')
def submit_job(cmd, job):
    lockfile = job.lockfile

    debug(f'Put lockfile in place for {lockfile}')
    lockfile.touch()

    info(f'submitting script {cmd}')
    ret = subprocess.run(cmd, check=True, capture_output=True)
    info(f'submission returned: {ret.stdout}')
    with open(lockfile, 'wb') as f:
        f.write(ret.stdout)


import time


class Task:

    def __init__(self, i):
        t0 = time.perf_counter()
        self.i = i

    def finished():
        t1 = time.perf_counter()
        if (t1 - t0) > (self.i + 5):
            print('Finished')
            return True
        return False


def job_task(cmd, job):
    lockfile = job.lockfile

    debug(f'Put lockfile in place for {lockfile}')
    lockfile.touch()

    info(f'submitting script {cmd}')
    ret = subprocess.run(cmd, check=True, capture_output=True)
    info(f'submission returned: {ret.stdout}')
    with open(lockfile, 'wb') as f:
        f.write(ret.stdout)

    while not job.is_completed:
        print(job, 'not completed')
        yield


import time


def scheduler(queue, cmd, max_jobs=10):
    tasks = deque()

    for _ in range(max_jobs):
        job = queue.popleft()
        task = job_task(cmd, job)
        tasks.append(task)

    while tasks:
        print('loop')
        time.sleep(0.5)
        task = tasks.popleft()
        try:
            next(task)  # Run to the next yield
            tasks.append(task)  # Reschedule
        except StopIteration:
            pass

        if queue and len(tasks) < max_jobs:
            job = queue.popleft()
            task = job_task(cmd, job)
            tasks.append(task)


def submission_script_ok(job):
    submission_script = job.submit_script
    if not submission_script.is_file():
        info('Did not found submission script %s ; Skipping directory...',
             submission_script)
        return False

    return True


def status_file_ok(job, *, force):
    status_file = job.status_file
    if status_file.exists() and not force:
        if not status_file.is_file():
            logger.warning('Status file %s is not a file', status_file)
        with open(status_file, 'r') as f:
            info('Status of %s: %s. To rerun enable the --force flag',
                 status_file, f.read())
        op_queue.add(action=lambda: None,
                     description=click.style('Not Submitting',
                                             fg='red',
                                             bold=True),
                     extra_description=f'{job} (reason: status file exists)')
        return False

    return True


def lockfile_ok(job, *, force):
    lockfile = job.lockfile
    if lockfile.exists() and not force:
        op_queue.add(action=lambda: None,
                     description=click.style('Not Submitting',
                                             fg='red',
                                             bold=True),
                     extra_description=f'{job} (reason: {lockfile} exists)')
        return False

    return True


def submit(*, force: bool, max_jobs: int, **kwargs):
    """submit. Function which implements the functionality to submit jobs to
    the cluster.

    Parameters
    ----------
    force : bool
        Force the submission even in the presence of lockfiles
    max_jobs : int
        Maximum number of jobs to submit at once
    """
    if not cfg.submit:
        raise Exception('submit field required in config file')

    debug('Submit config: %s', cfg.submit)

    workspace = WorkDirectory.parse_obj(cfg.workspace)
    runs = workspace.runs

    jobs = [Job(run.dirname) for run in runs]
    debug('Case directories: %s', jobs)

    n_submitted = 0

    submit_cmd = cfg.submit.submit_command.split()

    job_queue = deque()

    for job in jobs:
        if not submission_script_ok(job):
            continue
        if not status_file_ok(job, force=force):
            continue
        if not lockfile_ok(job, force=force):
            continue

        cmd: List[Any] = [*submit_cmd, str(job.submit_script)]

        job_queue.append(job)

        # submit_job(cmd, job)

        n_submitted += 1

        # if max_jobs and (n_submitted >= max_jobs):
        #     info(f'Max jobs ({max_jobs}) reached.')
        #     break

    print('scheduler')

    scheduler(job_queue, cmd=submit_cmd, max_jobs=max_jobs)
