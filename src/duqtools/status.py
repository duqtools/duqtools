import logging
from pathlib import Path
from time import sleep

from .config import cfg
from .jetto import read_namelist
from .models import WorkDirectory

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def has_submit_script(dir: Path) -> bool:
    return (dir / cfg.submit.submit_script_name).exists()


def has_status(dir: Path) -> bool:
    return (dir / cfg.status.status_file).exists()


def is_submitted(dir: Path) -> bool:
    return (dir / 'duqtools.submit.lock').exists()


def status_file_contains(dir: Path, msg) -> bool:
    sf = (dir / cfg.status.status_file)
    with open(sf, 'r') as f:
        content = f.read()
        debug('Checking if content of %s file: %s contains %s', sf, content,
              msg)
        return msg in content


def is_completed(dir: Path) -> bool:
    return status_file_contains(dir, cfg.status.msg_completed)


def is_failed(dir: Path) -> bool:
    return status_file_contains(dir, cfg.status.msg_failed)


def is_running(dir: Path) -> bool:
    return status_file_contains(dir, cfg.status.msg_running)


def completion_percentage(dir: Path) -> int:
    of = (dir / cfg.status.out_file)
    infile = (dir / cfg.status.in_file)
    if not of.exists():
        debug('%s does not exists, but the job is running', of)
        return 0
    if not infile.exists():
        debug('%s does not exists, but the job is running', infile)
        return 0

    with open(of, 'r') as f:
        lines = f.readlines()
        for i in range(len(lines) - 1, 0, -1):
            if 'STEP' in lines[i]:
                time = float(lines[i].split('=')[2].lstrip(' ').split(' ')[0])
                break
        else:
            time = 0.
    nml = read_namelist(infile)
    start = nml['nlist1']['tbeg']
    end = nml['nlist1']['tmax']
    return int(100 * (time - start) / (end - start))


class Status():

    dirs: list
    dirs_submit: list
    dirs_status: list
    dirs_failed: list
    dirs_running: list
    dirs_unknown: list

    def __init__(self):
        debug('Submit config: %s', cfg.submit)

        workspace = WorkDirectory.parse_obj(cfg.workspace)
        runs = workspace.runs

        self.dirs = [Path(run.dirname) for run in runs]
        debug('Case directories: %s', self.dirs)

        debug('Total number of directories: %i', len(self.dirs))
        self.update_status()

    def update_status(self):

        self.dirs_submit = [dir for dir in self.dirs if has_submit_script(dir)]
        self.dirs_status = [dir for dir in self.dirs if has_status(dir)]
        self.dirs_submitted = [dir for dir in self.dirs if is_submitted(dir)]

        self.dirs_completed = [
            dir for dir in self.dirs_status if is_completed(dir)
        ]
        self.dirs_failed = [dir for dir in self.dirs_status if is_failed(dir)]
        self.dirs_running = [
            dir for dir in self.dirs_status if is_running(dir)
        ]

        self.dirs_unknown = [
            dir for dir in self.dirs_status
            if not (dir in self.dirs_completed or dir in self.dirs_failed
                    or dir in self.dirs_running)
        ]

    def simple_status(self):
        """stateless status."""

        info('Total number of directories with submission script : %i',
             len(self.dirs_submit))
        info('      number of not submitted jobs                 : %i',
             (len(self.dirs_submit) - len(self.dirs_status)))
        info('Total number of directories with status     script : %i',
             len(self.dirs_status))
        info('Total number of directories with Completed status  : %i',
             len(self.dirs_completed))
        info('Total number of directories with Failed    status  : %i',
             len(self.dirs_failed))
        info('Total number of directories with Running   status  : %i',
             len(self.dirs_running))
        info('Total number of directories with Unknown   status  : %i',
             len(self.dirs_unknown))

    def progress_status(self):
        """Monitor the directory for status changes."""
        from tqdm import tqdm
        pbar_a = tqdm(total=len(self.dirs), position=0)
        pbar_a.set_description('Submitted jobs            ...')
        pbar_b = tqdm(total=len(self.dirs_submit), position=1)
        pbar_b.set_description('Running jobs              ...')
        pbar_c = tqdm(total=len(self.dirs_submit), position=2)
        pbar_c.set_description('Completed jobs            ...')
        pbar_d = tqdm(total=len(self.dirs_submit), position=3)
        pbar_d.set_description('Failed? jobs              ...')
        while len(self.dirs_completed) < len(self.dirs_submit):
            pbar_a.n = len(self.dirs_submitted)
            pbar_b.n = len(self.dirs_running)
            pbar_c.n = len(self.dirs_completed)
            pbar_d.n = len(self.dirs_failed) + len(self.dirs_unknown)
            pbar_a.refresh()
            pbar_b.refresh()
            pbar_c.refresh()
            pbar_d.refresh()
            sleep(5)
            self.update_status()

    def get_status(self, dir):
        if dir not in self.dirs_submit:
            return 'Unsubmitted '
        if dir in self.dirs_running:
            return 'Running     '
        if dir in self.dirs_failed:
            return 'FAILED      '
        if dir in self.dirs_completed:
            return 'COMPLETED   '
        return 'UNKNOWN'

    def detailed_status(self):
        from tqdm import tqdm
        """detailed_status of all separate runs."""
        pbars = []
        for i, dir in enumerate(self.dirs):
            pbars.append(tqdm(total=100, position=i))
            status = self.get_status(dir)
            pbars[-1].set_description(f'{dir.name:8s}, status: {dir.name:12s}')

        while len(self.dirs_completed) < len(self.dirs_submit):
            for i, dir in enumerate(self.dirs):
                status = self.get_status(dir)
                pbars[i].set_description(
                    f'{dir.name:8s}, status: {status:12s}')
                if dir in self.dirs_running:
                    pbars[i].n = completion_percentage(dir)
                pbars[i].refresh()
            sleep(5)
            self.update_status()


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
