import logging
from enum import Enum
from pathlib import Path

import click

from ..config import cfg

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug

cs = click.style

STATUS_SYMBOLS = {
    'no status': cs('_', fg='yellow'),
    'completed': cs('.', fg='green'),
    'failed': cs('f', fg='red'),
    'running': cs('r', fg='yellow'),
    'submitted': cs('s', fg='yellow'),
    'unknown': cs('u', fg='yellow')
}


class JobStatus(str, Enum):
    NOSTATUS = 'no status'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RUNNING = 'running'
    SUBMITTED = 'submitted'
    UNKNOWN = 'unknown'

    @property
    def symbol(self):
        return STATUS_SYMBOLS[self.value]

    @staticmethod
    def symbol_help():
        s = ', '.join(f'{code} : {status}'
                      for status, code in STATUS_SYMBOLS.items())
        return f'Status codes:\n{s}'


class Job:

    def __init__(self, dir: Path):
        self.dir = Path(dir).resolve()
        self.cfg = cfg

    def __repr__(self):
        run = str(self.dir)
        return f'{self.__class__.__name__}({run!r})'

    @staticmethod
    def status_symbol_help():
        """Return help string for status codes."""
        return JobStatus.symbol_help()

    @property
    def status_symbol(self):
        """One letter status symbol."""
        return self.status().symbol

    @property
    def has_submit_script(self) -> bool:
        return self.submit_script.exists()

    @property
    def has_status(self) -> bool:
        return self.status_file.exists()

    @property
    def is_submitted(self) -> bool:
        return (self.dir / 'duqtools.submit.lock').exists()

    def status(self) -> str:
        if not self.has_status:
            return JobStatus.NOSTATUS

        sf = self.status_file
        with open(sf) as f:
            content = f.read()
            if self.cfg.status.msg_completed in content:
                return JobStatus.COMPLETED
            elif self.cfg.status.msg_failed in content:
                return JobStatus.FAILED
            elif self.cfg.status.msg_running in content:
                return JobStatus.RUNNING

        if self.is_submitted:
            return JobStatus.SUBMITTED

        return JobStatus.UNKNOWN

    @property
    def is_completed(self) -> bool:
        return self.status() == JobStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status() == JobStatus.FAILED

    @property
    def is_running(self) -> bool:
        return self.status() == JobStatus.RUNNING

    @property
    def in_file(self) -> Path:
        return self.dir / self.cfg.status.in_file

    @property
    def out_file(self) -> Path:
        return self.dir / self.cfg.status.out_file

    @property
    def status_file(self) -> Path:
        return self.dir / self.cfg.status.status_file

    @property
    def submit_script(self) -> Path:
        return self.dir / self.cfg.submit.submit_script_name

    @property
    def lockfile(self) -> Path:
        return self.dir / 'duqtools.submit.lock'

    def submit(self):
        from ..system import get_system
        debug(f'Put lockfile in place for {self.lockfile}')
        self.lockfile.touch()

        get_system().submit_job(self)

    def start(self):
        click.echo(f'Submitting {self}\033[K')
        self.submit()

        while not self.has_status:
            yield

        while self.is_running:
            yield
