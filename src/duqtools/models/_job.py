from __future__ import annotations

import logging
import time
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..config import Config

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

    def __init__(self, path: Path, *, cfg: Config):
        """This class handles job status and submission.

        Parameters
        ----------
        path : Path
            Directory for simulation or model run.
        cfg : Optional[Config], optional
            Duqtools config, defaults to global config if unspecified.
        """
        #self.path = Path(path).resolve()
        self.path = Path(path)
        self.cfg = cfg

    def __repr__(self):
        run = str(self.path)
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
        """Return true if directory has submit script."""
        return self.submit_script.exists()

    @property
    def has_status(self) -> bool:
        """Return true if a status file exists."""
        return self.status_file.exists()

    @property
    def is_submitted(self) -> bool:
        """Return true if the job has been submitted."""
        return (self.path / 'duqtools.submit.lock').exists()

    def status(self) -> str:
        """Return the status of the job."""
        if not self.has_status:
            return JobStatus.NOSTATUS

        sf = self.status_file
        with open(sf) as f:
            content = f.read()
            if self.cfg.system.msg_completed in content:
                return JobStatus.COMPLETED
            elif self.cfg.system.msg_failed in content:
                return JobStatus.FAILED
            elif self.cfg.system.msg_running in content:
                return JobStatus.RUNNING

        if self.is_submitted:
            return JobStatus.SUBMITTED

        return JobStatus.UNKNOWN

    @property
    def is_completed(self) -> bool:
        """Return true if the job has been completed succesfully."""
        return self.status() == JobStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Return true if the job has failed."""
        return self.status() == JobStatus.FAILED

    @property
    def is_running(self) -> bool:
        """Return true if the job is running."""
        return self.status() == JobStatus.RUNNING

    @property
    def is_done(self) -> bool:
        """Return true if the job is done (completed or failed)."""
        return self.status() in (JobStatus.COMPLETED or JobStatus.FAILED)

    @property
    def in_file(self) -> Path:
        """Return path to the input file for the job."""
        return self.path / self.cfg.system.in_file

    @property
    def out_file(self) -> Path:
        """Return path to the output file for the job."""
        return self.path / self.cfg.system.out_file

    @property
    def status_file(self) -> Path:
        """Return the path of the status file."""
        return self.path / self.cfg.system.status_file

    @property
    def submit_script(self) -> Path:
        """Return the path of the submit script."""
        return self.path / self.cfg.system.submit_script_name

    @property
    def lockfile(self) -> Path:
        """Return the path of the lockfile."""
        return self.path / 'duqtools.submit.lock'

    def submit(self):
        """Submit job."""
        from duqtools.systems import get_system
        debug(f'Put lockfile in place for {self.lockfile}')
        self.lockfile.touch()

        get_system(self.cfg).submit_job(self)

    def start(self):
        """Submit job and return generate that raises StopIteration when
        done."""
        click.echo(f'Submitting {self}\033[K')
        self.submit()

        while self.status() in (JobStatus.RUNNING, JobStatus.NOSTATUS):
            yield

    def wait_until_done(self, time_step: float = 1.0):
        """Submit task and wait until done.

        Parameters
        ----------
        time_step : float, optional
            Time in seconds step between status updates.
        """
        while self.status() in (JobStatus.RUNNING, JobStatus.NOSTATUS):
            time.sleep(time_step)
