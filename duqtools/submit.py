import logging
import subprocess
from pathlib import Path
from typing import Any, List

from duqtools.config import cfg

logger = logging.getLogger(__name__)
info, debug = logger.info, logger.debug


def submit(force: bool = False, **kwargs):
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

    runs = cfg.workspace.runs

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

        status_file = run_dir / cfg.submit.status_file
        if status_file.exists() and not force:
            if not status_file.is_file():
                info('Status file %s is not a file', status_file)
            with open(status_file, 'r') as f:
                info('Status of %s: %s. To rerun enable the --force flag',
                     status_file, f.read())
            info('Skipping directory %s ; due to existing status file',
                 run_dir)
            continue

        lockfile = run_dir / 'duqtools.submit.lock'
        if lockfile.exists() and not force:
            info(
                'Skipping %s, lockfile exists, enable --force to submit again',
                run_dir)
            continue

        debug('Put lockfile in place for %s', submission_script)
        lockfile.touch()

        cmd: List[Any] = [*cfg.submit.submit_command, submission_script]

        info('submitting script %s', str(cmd))
        ret = subprocess.run(cmd, check=True, capture_output=True)
        info('submission returned: %s', ret.stdout)
        with open(lockfile, 'wb') as f:
            f.write(ret.stdout.split()[-1])
