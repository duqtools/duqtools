import logging
from time import sleep

from ._job import Job
from .config import cfg
from .jettoduqtools import JettoSettingsManager
from .models import WorkDirectory

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug
stream = logging.StreamHandler()
stream.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(stream)


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

        workspace = WorkDirectory.parse_obj(cfg.workspace)
        runs = workspace.runs

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

        self.set_status()

        infile = job.in_file
        if not infile.exists():
            debug('%s does not exist, but the job is running', infile)
            return 0

        jsetmanager = JettoSettingsManager.from_directory(job.dir)

        self.start = jsetmanager.tstart
        self.end = jsetmanager.tend
        self.time = self.start

        self.finished = False

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

    def get_lines(self):
        if not self.outfile:
            of = self.job.out_file
            if not of.exists():
                debug('%s does not exists, but the job is running', of)
                return []
            self.output_file = open(of, 'r')
        return self.output_file.readlines()

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

        lines = self.get_lines()
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].startswith(' STEP'):
                self.time = float(
                    lines[i].split('=')[2].lstrip(' ').split(' ')[0])
                break

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
