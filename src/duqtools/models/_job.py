import logging
from pathlib import Path

import click

from ..config import cfg

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


class Job:

    def __init__(self, dir: Path):
        self.dir = Path(dir)

    def __repr__(self):
        run = str(self.dir)
        return f'{self.__class__.__name__}({run!r})'

    @property
    def has_submit_script(self) -> bool:
        return self.submit_script.exists()

    @property
    def has_status(self) -> bool:
        return self.status_file.exists()

    @property
    def is_submitted(self) -> bool:
        return (self.dir / 'duqtools.submit.lock').exists()

    def status_file_contains(self, msg) -> bool:
        sf = self.status_file
        with open(sf) as f:
            content = f.read()
            debug('Checking if content of %s file: %s contains %s', sf,
                  content, msg)
            return msg in content

    @property
    def is_completed(self) -> bool:
        return self.status_file_contains(cfg.status.msg_completed)

    @property
    def is_failed(self) -> bool:
        return self.status_file_contains(cfg.status.msg_failed)

    @property
    def is_running(self) -> bool:
        return self.status_file_contains(cfg.status.msg_running)

    @property
    def in_file(self) -> Path:
        return self.dir / cfg.status.in_file

    @property
    def out_file(self) -> Path:
        return self.dir / cfg.status.out_file

    @property
    def status_file(self) -> Path:
        return self.dir / cfg.status.status_file

    @property
    def submit_script(self) -> Path:
        return self.dir / cfg.submit.submit_script_name

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
