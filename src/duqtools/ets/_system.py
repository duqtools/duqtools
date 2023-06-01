import logging
import shutil
import stat
import subprocess as sp
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..config import Config
from ..ids import ImasHandle
from ..models import AbstractSystem, Job
from ..operations import add_to_op_queue

logger = logging.getLogger(__name__)

SCRIPT_TEMPLATE = 'kepler -runwf -nogui -redirectgui {job.path} ' \
    '-paramFile {job.path}/{cfg.create.template.name} ' \
    '{cfg.system.ets_xml} ' \
    '> {job.path}/ets6.out ' \
    '2> {job.path}/ets6.err'

BATCH_TEMPLATE = '\n'.join([
    'module purge', 'module load cineca', 'module load ets6',
    'module switch {cfg.system.kepler_module}',
    'kepler_load {cfg.system.kepler_load}', '{scripts}'
])


class Ets6System(AbstractSystem):
    """System that can be used to create runs for ets."""

    def get_runs_dir(self) -> Path:
        return Path()

    @add_to_op_queue('Writing new batchfile', '{run_dir.name}', quiet=True)
    def write_batchfile(self, run_dir: Path, cfg: Config):
        job = Job(run_dir, cfg=cfg)
        script = SCRIPT_TEMPLATE.format(job=job, cfg=self.cfg)
        batchfile = '\n'.join([
            '#!/bin/sh', f'#SBATCH -J duqtools.ets6.{run_dir.name}',
            f'#SBATCH -o {run_dir}/slurm.out',
            f'#SBATCH -e {run_dir}/slurm.err', '#SBATCH -p gw', '#SBATCH -N 1',
            '#SBATCH -n 1', '#SBATCH -t 1:00:00', ''
        ]) + BATCH_TEMPLATE.format(cfg=self.cfg, scripts=script)

        run_ets6 = Path(run_dir / 'run.sh')
        with open(run_ets6, 'w') as f:
            f.write(batchfile)

    def write_array_batchfile(self, jobs: Sequence[Job], max_jobs: int,
                              max_array_size: int):
        scripts = '\n'.join(
            [SCRIPT_TEMPLATE.format(job=job, cfg=self.cfg) for job in jobs])

        batchfile = '#!/bin/sh\n' + BATCH_TEMPLATE.format(cfg=self.cfg,
                                                          scripts=scripts)

        array = Path('duqtools_array.sh')
        with open(array, 'w') as f:
            f.write(batchfile)
        array.chmod(array.stat().st_mode | stat.S_IXUSR)

    def submit_job(self, job: Job):
        if not job.has_submit_script:
            raise FileNotFoundError(job.submit_script)

        submit_cmd = self.cfg.submit.submit_command.split()
        cmd: list[Any] = [*submit_cmd, str(job.submit_script)]

        logger.info(f'submitting via {cmd}')

        ret = sp.run(cmd, check=True, capture_output=True)
        logger.info('submission returned: ' + str(ret.stdout))
        with open(job.lockfile, 'wb') as f:
            f.write(ret.stdout)

    @add_to_op_queue('Submit single array job', 'duqtools_array.sh')
    def submit_array(self, jobs: Sequence[Job], max_jobs: int,
                     max_array_size: int, **kwargs):
        for job in jobs:
            job.lockfile.touch()

        logger.info('writing duqtools_slurm_array.sh file')
        self.write_array_batchfile(jobs, max_jobs, max_array_size)

        self.cfg.submit.submit_command.split()
        cmd: list[str] = ['./duqtools_array.sh']

        logger.info(f'Submitting script via: {cmd}')

        sp.Popen(cmd, )

        for job in jobs:
            with open(job.lockfile, 'w') as f:
                f.write('being run')

    @add_to_op_queue('Copying template to', '{target_drc}', quiet=True)
    def copy_from_template(self, source_drc: Path, target_drc: Path):
        shutil.copy(source_drc, target_drc)

    def imas_from_path(self, template_drc: Path) -> ImasHandle:
        raise NotImplementedError('imas_from_path')

    @add_to_op_queue('Updating imas locations of', '{run}', quiet=True)
    def update_imas_locations(self, run: Path, inp: ImasHandle,
                              out: ImasHandle, cfg_filename: Path):
        #raise NotImplementedError('update_imas_location')
        new_input = []
        with open(run / cfg_filename) as f:
            for line in f.readlines():
                if line.startswith('START.output_run'):
                    new_input.append('START.output_run = ' + str(out.run) +
                                     '\n')
                elif line.startswith('START.input_run'):
                    new_input.append('START.input_run = ' + str(inp.run) +
                                     '\n')
                elif line.startswith('START.shot_number'):
                    new_input.append('START.shot_number = ' + str(inp.shot) +
                                     '\n')
                elif line.startswith('START.user_name'):
                    new_input.append('START.user_name = ' + str(out.user) +
                                     '\n')
                else:
                    new_input.append(line)
        with open(run / cfg_filename, 'w') as f:
            f.writelines(new_input)

    def get_data_in_handle(
        self,
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ):
        """Get handle for data input."""
        return ImasHandle(
            user=options.user,
            db=options.imasdb,
            shot=source.shot,
            run=options.run_in_start_at + seq_number,
        )

    def get_data_out_handle(
        self,
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ):
        """Get handle for data output."""
        return ImasHandle(
            user=options.user,
            db=options.imasdb,
            shot=source.shot,
            run=options.run_out_start_at + seq_number,
        )
