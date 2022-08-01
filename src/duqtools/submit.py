import logging
import subprocess
from pathlib import Path
from typing import Any, List

import click

from .config import cfg
from .models import WorkDirectory
from .operations import add_to_op_queue, op_queue

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


@add_to_op_queue('Submitting', '{run_dir}')
def submit_job(lockfile, cmd, run_dir):
    debug(f'Put lockfile in place for {lockfile}')
    lockfile.touch()

    info(f'submitting script {cmd}')
    ret = subprocess.run(cmd, check=True, capture_output=True)
    info(f'submission returned: {ret.stdout}')
    with open(lockfile, 'wb') as f:
        f.write(ret.stdout)


def submit(*, force: bool, **kwargs):
    """submit. Function which implements the functionality to submit jobs to
    the cluster.

    Parameters
    ----------
    force : bool
        force the submission even in the presence of lockfiles
    """

    if not cfg.submit:
        raise Exception('submit field required in config file')

    debug('Submit config: %s', cfg.submit)

    workspace = WorkDirectory.parse_obj(cfg.workspace)
    runs = workspace.runs

    run_dirs = [Path(run.dirname) for run in runs]
    debug('Case directories: %s', run_dirs)

    for run_dir in run_dirs:
        submission_script = run_dir / cfg.submit.submit_script_name
        if submission_script.is_file():
            info('Found submission script: %s ; Ready for submission',
                 submission_script)
        else:
            info('Did not found submission script %s ; Skipping directory...',
                 submission_script)
            continue

        status_file = run_dir / cfg.status.status_file
        if status_file.exists() and not force:
            if not status_file.is_file():
                logger.warning('Status file %s is not a file', status_file)
            with open(status_file, 'r') as f:
                info('Status of %s: %s. To rerun enable the --force flag',
                     status_file, f.read())
            op_queue.add(
                action=lambda: None,
                description=click.style('Not Submitting', fg='red', bold=True),
                extra_description=f'{run_dir}, statusfile already exists,'
                ' enable --force to override')
            continue

        lockfile = run_dir / 'duqtools.submit.lock'
        if lockfile.exists() and not force:
            op_queue.add(
                action=lambda: None,
                description=click.style('Not Submitting', fg='red', bold=True),
                extra_description=f'{run_dir}, {lockfile} already exists,'
                ' enable --force to override')
            continue

        submit_cmd = cfg.submit.submit_command.split()
        cmd: List[Any] = [*submit_cmd, str(submission_script)]

        submit_job(lockfile, cmd, run_dir)
