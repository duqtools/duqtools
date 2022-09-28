import logging
import subprocess as sp
from typing import Any, List

from jetto_tools import config
from jetto_tools import job as jetto_job
from jetto_tools import template

from .config import cfg
from .models import AbstractSystem, Job
from .operations import add_to_op_queue

logger = logging.getLogger(__name__)


class JettoSystem(AbstractSystem):

    @staticmethod
    def submit_job(job: Job):
        if cfg.submit.submit_system == 'slurm':
            JettoSystem.submit_slurm(job)
        elif cfg.submit.submit_system == 'prominence':
            JettoSystem.submit_prominence(job)
        else:
            raise NotImplementedError(
                'submission type {cfg.submit.submit_system}'
                ' not implemented')

    @staticmethod
    @add_to_op_queue('Submitting job', '{job}', quiet=True)
    def submit_slurm(job: Job):
        if not job.has_submit_script:
            raise FileNotFoundError(job.submit_script)

        submit_cmd = cfg.submit.submit_command.split()
        cmd: List[Any] = [*submit_cmd, str(job.submit_script)]

        logger.info(f'submitting script via slurm {cmd}')

        ret = sp.run(cmd, check=True, capture_output=True)
        logger.info('submission returned: ' + str(ret.stdout))
        with open(job.lockfile, 'wb') as f:
            f.write(ret.stdout)

    @staticmethod
    @add_to_op_queue('Submitting job via prominence', '{job}', quiet=True)
    def submit_prominence(job: Job):

        jetto_template = template.from_directory(job.dir)
        jetto_config = config.RunConfig(jetto_template)
        jetto_manager = jetto_job.JobManager()

        _ = jetto_manager.submit_job_to_prominence(jetto_config, job.dir)
