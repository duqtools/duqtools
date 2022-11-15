import logging
import subprocess as sp
from time import sleep

from jetto_tools import config, template

from .config import cfg
from .jetto._system import jetto_lookup
from .models import Job, Locations

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug
stream = logging.StreamHandler()
stream.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(stream)


class StatusError(Exception):
    ...


class Status():

    jobs: list
    jobs_submit: list
    jobs_submitted: list
    jobs_status: list
    jobs_failed: list
    jobs_running: list
    jobs_unknown: list

    def __init__(self):
        debug('Submit config: %s', cfg.submit)

        runs = Locations().runs

        self.jobs = [Job(run.dirname) for run in runs]
        debug('Case directories: %s', self.jobs)

        debug('Total number of directories: %i', len(self.jobs))

    def update_status(self):

        self.jobs_submit = [job for job in self.jobs if job.has_submit_script]
        self.jobs_status = [job for job in self.jobs if job.has_status]
        self.jobs_submitted = [job for job in self.jobs if job.is_submitted]

        self.jobs_completed = [
            job for job in self.jobs_status if job.is_completed
        ]
        self.jobs_failed = [job for job in self.jobs_status if job.is_failed]
        self.jobs_running = [job for job in self.jobs_status if job.is_running]

        self.jobs_unknown = [
            job for job in self.jobs_status
            if not (job in self.jobs_completed or job in self.jobs_failed
                    or job in self.jobs_running)
        ]

    def simple_status(self):
        """stateless status."""

        self.update_status()
        info('Total number of directories with submission script : %i',
             len(self.jobs_submit))
        info('      number of not submitted jobs                 : %i',
             (len(self.jobs_submit) - len(self.jobs_status)))
        info('Total number of directories with status     script : %i',
             len(self.jobs_status))
        info('Total number of directories with Completed status  : %i',
             len(self.jobs_completed))
        info('Total number of directories with Failed    status  : %i',
             len(self.jobs_failed))
        info('Total number of directories with Running   status  : %i',
             len(self.jobs_running))
        info('Total number of directories with Unknown   status  : %i',
             len(self.jobs_unknown))

    def progress_status(self):
        """Monitor the directory for status changes."""
        from tqdm import tqdm
        pbar_a = tqdm(total=len(self.jobs), position=0)
        pbar_a.set_description('Submitted jobs            ...')
        pbar_b = tqdm(total=len(self.jobs_submit), position=1)
        pbar_b.set_description('Running jobs              ...')
        pbar_c = tqdm(total=len(self.jobs_submit), position=2)
        pbar_c.set_description('Completed jobs            ...')
        pbar_d = tqdm(total=len(self.jobs_submit), position=3)
        pbar_d.set_description('Failed? jobs              ...')
        while len(self.jobs_completed) < len(self.jobs_submit):
            pbar_a.n = len(self.jobs_submitted)
            pbar_b.n = len(self.jobs_running)
            pbar_c.n = len(self.jobs_completed)
            pbar_d.n = len(self.jobs_failed) + len(self.jobs_unknown)
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

        jetto_template = template.from_directory(job.dir)
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

        More info: https://github.com/duqtools/duqtools/issues/337
        """
        msg = ('Cannot show detailed status, `nlist2.KWMAIN` flag'
               ' is not set to 1 in `{self.job.status_file}`')
        if jetto_config['kwmain'] != 1:
            raise StatusError(msg)

    def set_status(self):
        if not self.job.has_status:
            status = 'No status'
        elif not self.job.is_submitted:
            status = 'Unsubmitted '
        elif self.job.is_running:
            status = 'Running     '
        elif self.job.is_failed:
            status = 'FAILED      '
        elif self.job.is_completed:
            status = 'COMPLETED   '
        else:
            status = 'UNKNOWN'

        self.pbar.set_description(
            f'{self.job.dir.name:8s}, status: {status:12s}')
        self.pbar.refresh()

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
        self.set_status()
        if self.job.has_status:
            if self.job.is_completed or self.job.is_failed:
                self.pbar.n = 100 if self.job.is_completed else 0
                self.pbar.refresh()
                self.finished = True
                return
            if not self.job.is_running:
                return

        steptime = self.get_steptime()
        if steptime:
            self.time = steptime

        self.pbar.n = int(100 * (self.time - self.start) /
                          (self.end - self.start))
        self.pbar.refresh()


def status(*, progress: bool, detailed: bool, **kwargs):
    """Show status of runs.

    Parameters
    ----------
    progress : bool
        Show progress bar.
    detailed : bool
        Show detailed progress for every job.
    """

    tracker = Status()

    if detailed:
        tracker.detailed_status()
    elif progress:
        tracker.progress_status()
    else:
        tracker.simple_status()
