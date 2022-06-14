import logging
import subprocess
from os import scandir
from pathlib import Path

from duqtools.config import Config as cfg

logger = logging.getLogger(__name__)


def submit(**kwargs):
    """submit.

    Function which implements the functionality to submit jobs to the
    cluster
    """

    args = kwargs.args

    if not cfg().submit:
        raise Exception('submit field required in config file')
    logger.debug('Submit config: %s' % cfg().submit)

    run_dirs = [
        Path(entry) for entry in scandir(cfg().workspace) if entry.is_dir()
    ]
    logger.debug('Case directories: %s' % run_dirs)

    for run_dir in run_dirs:
        submission_script = run_dir / cfg().submit.submit_script_name
        if submission_script.is_file():
            logger.info('Found submission script: %s ; Ready for submission' %
                        submission_script)
        else:
            logger.debug(
                'Did not found submission script %s ; Skipping directory...' %
                submission_script)
            continue

        status_file = run_dir / cfg().submit.status_file
        if status_file.exists() and not args.force:
            if not status_file.is_file():
                logger.error('Status file %s is not a file' % status_file)
            with open(status_file, 'r') as f:
                logger.info(
                    'Status of %s: %sTo rerun please enable the force flag' %
                    (status_file, f.read()))
            logger.info('Skipping directory %s ; due to existing status file' %
                        run_dir)
            continue

        logger.info('executing: sbatch %s' % submission_script)
        ret = subprocess.run(['sbatch', submission_script],
                             check=True,
                             capture_output=True)
        logger.info('sbatch returned: %s' % ret.stdout)
