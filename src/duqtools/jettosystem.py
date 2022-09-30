import logging
import stat
import subprocess as sp
from typing import Any, List, Sequence

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
    def submit_prominence(job: Job):

        jetto_template = template.from_directory(job.dir)
        jetto_config = config.RunConfig(jetto_template)
        jetto_manager = jetto_job.JobManager()

        _ = jetto_manager.submit_job_to_prominence(jetto_config, job.dir)

    @staticmethod
    def submit_array(jobs: Sequence[Job]):
        if cfg.submit.submit_system == 'slurm':
            JettoSystem.submit_array_slurm(jobs)
        else:
            raise NotImplementedError(
                'array submission type {cfg.submit.submit_system}'
                ' not implemented')

    @staticmethod
    @add_to_op_queue('Submit single array job', 'duqtools_slurm_array.sh')
    def submit_array_slurm(jobs: Sequence[Job]):
        for job in jobs:
            job.submit_script.chmod(job.submit_script.stat().st_mode
                                    | stat.S_IXUSR)
            (job.dir / 'rjettov').chmod((job.dir / 'rjettov').stat().st_mode
                                        | stat.S_IXUSR)
            job.lockfile.touch()

        # Get the first jobs submission script as a template
        template = []
        for line in open(jobs[0].submit_script, 'r').readlines():
            if line.startswith('#SBATCH') or line.startswith('#!'):
                template.append(line)
        # Append our own options, later options have precedence
        template.append('#SBATCH -o duqtools_slurm_array.out\n')
        template.append('#SBATCH -e duqtools_slurm_array.err\n')
        template.append('#SBATCH --array=0-' + str(len(jobs) - 1) + '\n')
        template.append('#SBATCH -J duqtools_array\n')

        scripts = [str(job.submit_script) for job in jobs]
        script_str = 'scripts=(' + ' '.join(scripts) + ')\n'
        template.append(script_str)

        template.append('echo executing ${scripts[$SLURM_ARRAY_TASK_ID]}\n')
        template.append('${scripts[$SLURM_ARRAY_TASK_ID]} || true\n')

        logger.info('writing duqtools_slurm_array.sh file')
        with open('duqtools_slurm_array.sh', 'w') as f:
            f.write(''.join(template))

        submit_cmd = cfg.submit.submit_command.split()
        cmd: List[Any] = [*submit_cmd, 'duqtools_slurm_array.sh']

        logger.info(f'Submitting script via: {cmd}')

        ret = sp.run(cmd, check=True, capture_output=True)
        logger.info('submission returned: ' + str(ret.stdout))
        with open(job.lockfile, 'wb') as f:
            f.write(ret.stdout)
