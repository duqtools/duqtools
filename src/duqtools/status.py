from __future__ import annotations

import logging
import subprocess as sp
from collections import Counter
from time import sleep
from typing import Sequence

from jetto_tools import config, template

from .config import Config
from .models import Job, JobStatus, Locations
from .systems.jetto._system import jetto_lookup

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug
stream = logging.StreamHandler()
stream.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(stream)


class StatusError(Exception):
    ...


class Status():

    jobs: Sequence[Job]
    jobs_submit: int
    jobs_submitted: int
    jobs_status: int
    jobs_failed: int
    jobs_running: int
    jobs_unknown: int

    def __init__(self, jobs=Sequence[Job]):
        self.jobs = jobs

        debug('Case directories: %s', self.jobs)

        debug('Total number of jobs: %i', len(self.jobs))

    def update_status(self):

        self.n_submit_script = sum(job.has_submit_script for job in self.jobs)
        self.n_status = sum(job.has_status for job in self.jobs)

        counter = Counter(job.status() for job in self.jobs)

        self.n_submitted = counter[JobStatus.SUBMITTED]
        self.n_completed = counter[JobStatus.COMPLETED]
        self.n_running = counter[JobStatus.RUNNING]
        self.n_failed = counter[JobStatus.FAILED]
        self.n_unknown = counter[JobStatus.UNKNOWN]

    def simple_status(self):
        """Stateless status."""
        self.update_status()

        msg = 'Total number of directories with %-17s : %i'

        info(msg, 'submit script', self.n_submit_script)
        info(msg, 'unsubmitted jobs', self.n_submit_script - self.n_status)
        info(msg, 'status script', self.n_status)
        info(msg, 'completed status', self.n_completed)
        info(msg, 'failed status', self.n_failed)
        info(msg, 'running status', self.n_running)
        info(msg, 'unknown status', self.n_unknown)

    def progress_status(self):
        """Monitor the directory for status changes."""
        self.update_status()

        from tqdm import tqdm
        pbar_a = tqdm(total=len(self.jobs), position=0)
        pbar_a.set_description('Submitted jobs            ...')
        pbar_b = tqdm(total=self.n_submit_script, position=1)
        pbar_b.set_description('Running jobs              ...')
        pbar_c = tqdm(total=self.n_submit_script, position=2)
        pbar_c.set_description('Completed jobs            ...')
        pbar_d = tqdm(total=self.n_submit_script, position=3)
        pbar_d.set_description('Failed? jobs              ...')
        while self.n_completed < self.n_submit_script:
            pbar_a.n = self.n_submitted
            pbar_b.n = self.n_running
            pbar_c.n = self.n_completed
            pbar_d.n = self.n_failed + self.n_unknown
            pbar_a.refresh()
            pbar_b.refresh()
            pbar_c.refresh()
            pbar_d.refresh()
            sleep(5)
            self.update_status()

    def detailed_status(self):
        from tqdm import tqdm
        """detailed_status of all separate runs."""
        monitors = []
        for i, job in enumerate(self.jobs):
            pbar = tqdm(total=100, position=i)
            monitor = Monitor(pbar=pbar, job=job)
            monitors.append(monitor)

        while not all([monitor.finished for monitor in monitors]):
            for monitor in monitors:
                monitor.update()
            sleep(5)


class Monitor():
    """Convenience class to keep track of submissions and update progress
    bars."""

    def __init__(self, pbar, job):
        self.pbar = pbar
        self.job = job
        self.outfile = None

        jetto_template = template.from_directory(job.path)
        jetto_template.lookup.update(jetto_lookup)
        jetto_config = config.RunConfig(jetto_template)

        self.check_kwmain_flag(jetto_config)

        infile = job.in_file
        if not infile.exists():
            debug('%s does not exist, but the job is running', infile)
            return

        self.start = jetto_config.start_time
        self.end = jetto_config.end_time
        self.time = self.start

        self.finished = False

        self.set_status()

    def check_kwmain_flag(self, jetto_config):
        """Check for NLIST2/KWMAIN in jetto.jset. If this flag is not set, the
        output in `job.out_file` does not contain the output that is grepped
        for the progress.

        More info:
        https://github.com/duqtools/duqtools/issues/337
        """
        msg = ('Cannot show detailed status, `nlist2.KWMAIN` flag'
               ' is not set to 1 in `{self.job.status_file}`')
        if jetto_config['kwmain'] != 1:
            raise StatusError(msg)

    def set_status(self):
        status = self.job.status()

        self.pbar.set_description(f'{self.job.path.name:8s}, {status:12s}')
        self.pbar.refresh()

        return status

    def get_steptime(self):
        if not self.job.out_file.exists():
            debug(
                f'{self.job.out_file} does not exists, but the job is running')
            return None

        of = self.job.out_file
        cmd = f'tac {of} | grep -m 1 ^\\s*STEP'
        ret = sp.run(cmd, shell=True, capture_output=True)
        if len(ret.stdout) > 0:
            return float(ret.stdout.split('=')[2].lstrip(' ').split(' ')[0])
        return None

    def update(self):
        status = self.set_status()
        if status in (JobStatus.COMPLETED, JobStatus.FAILED):
            self.pbar.n = 100 if status == JobStatus.COMPLETED else 0
            self.pbar.refresh()
            self.finished = True
            return
        if not status == JobStatus.RUNNING:
            return

        steptime = self.get_steptime()
        if steptime:
            self.time = steptime

        self.pbar.n = int(100 * (self.time - self.start) /
                          (self.end - self.start))
        self.pbar.refresh()


def status(*,
           cfg: Config,
           progress: bool = False,
           detailed: bool = False,
           **kwargs):
    """Show status of runs.

    Parameters
    ----------
    progress : bool
        Show progress bar.
    detailed : bool
        Show detailed progress for every job.
    """
    debug('Submit config: %s', cfg.system)

    runs = Locations(cfg=cfg).runs
    jobs = [Job(run.dirname, cfg=cfg) for run in runs]

    tracker = Status(jobs)

    if detailed:
        tracker.detailed_status()
    elif progress:
        tracker.progress_status()
    else:
        tracker.simple_status()

    return tracker


def status_api(config: dict, **kwargs):
    """Wrapper around status for python api."""
    cfg = Config.from_dict(config)
    return status(cfg=cfg, **kwargs)
