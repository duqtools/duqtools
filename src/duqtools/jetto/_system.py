import logging
import os
import shutil
import stat
import subprocess as sp
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, List, Optional

from jetto_tools import config, jset, lookup, namelist, template
from jetto_tools import job as jetto_job
from jetto_tools.template import _EXTRA_FILE_REGEXES

from ..config import cfg
from ..ids import ImasHandle
from ..models import AbstractSystem, Job, Locations
from ..operations import add_to_op_queue
from ..schema import JettoVar
from ._jettovar_to_json import jettovar_to_json
from ._llcmd import write_batchfile as jetto_write_batchfile

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files

logger = logging.getLogger(__name__)

lookup_file = files('duqtools.data') / 'jetto_tools_lookup.json'
jetto_lookup = lookup.from_file(lookup_file)


class BaseJettoSystem(AbstractSystem):

    @staticmethod
    def get_runs_dir() -> Path:
        path = Locations().jruns_path
        runs_dir = cfg.create.runs_dir  # type: ignore
        if not runs_dir:
            abs_cwd = str(Path.cwd().resolve())
            abs_jruns = str(path.resolve())
            # Check if jruns is parent dir of current dir
            if abs_cwd.startswith(abs_jruns):
                runs_dir = Path()
            else:  # jruns is somewhere else
                count = 0
                while True:  # find the next free folder
                    runs_dir = f'duqtools_experiment_{count:04d}'
                    if not (path / runs_dir).exists():
                        break
                    count = count + 1
        return path / runs_dir

    @staticmethod
    @add_to_op_queue('Writing new batchfile', '{run_dir.name}', quiet=True)
    def write_batchfile(run_dir: Path):
        jetto_jset = jset.read(run_dir / 'jetto.jset')

        jetto_write_batchfile(run_dir, jetto_jset)

    @staticmethod
    def submit_job(job: Job):
        if cfg.submit.submit_system == 'slurm':
            JettoSystem.submit_slurm(job)
        elif cfg.submit.submit_system == 'docker':
            JettoSystem.submit_docker(job)
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
        cmd: list[Any] = [*submit_cmd, str(job.submit_script)]

        logger.info(f'submitting script via slurm {cmd}')

        ret = sp.run(cmd, check=True, capture_output=True)
        logger.info('submission returned: ' + str(ret.stdout))
        with open(job.lockfile, 'wb') as f:
            f.write(ret.stdout)

    @staticmethod
    def submit_docker(job: Job):

        jetto_template = template.from_directory(job.dir)
        jetto_config = config.RunConfig(jetto_template)
        jetto_manager = jetto_job.JobManager()
        extra_volumes = {
            job.dir.parent / 'imasdb': {
                'bind': '/opt/imas/shared/imasdb',
                'mode': 'rw'
            },
        }

        os.environ['RUNS_HOME'] = os.getcwd()
        _ = jetto_manager.submit_job_to_docker(jetto_config,
                                               job.dir,
                                               image=cfg.submit.docker_image,
                                               extra_volumes=extra_volumes)
        job.lockfile.touch()

    @staticmethod
    def submit_prominence(job: Job):
        jetto_template = template.from_directory(job.dir)
        jetto_config = config.RunConfig(jetto_template)
        jetto_manager = jetto_job.JobManager()

        os.environ['RUNS_HOME'] = os.getcwd()
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
            job.lockfile.touch()

        # Get the first jobs submission script as a template
        template = []
        for line in open(jobs[0].submit_script).readlines():
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
        cmd: list[Any] = [*submit_cmd, 'duqtools_slurm_array.sh']

        logger.info(f'Submitting script via: {cmd}')

        ret = sp.run(cmd, check=True, capture_output=True)
        logger.info('submission returned: ' + str(ret.stdout))
        with open(job.lockfile, 'wb') as f:
            f.write(ret.stdout)

    @staticmethod
    def _apply_patches_to_template(jetto_template: template.Template):
        """Apply settings that are necessary for duqtools to function."""
        # Force output of IDS data
        # https://github.com/duqtools/duqtools/issues/343
        jetto_template.jset._settings['JobProcessingPanel.selIdsRunid'] = False

    @staticmethod
    @add_to_op_queue('Copying template to', '{target_drc}', quiet=True)
    def copy_from_template(source_drc: Path, target_drc: Path):
        jetto_jset = jset.read(source_drc / 'jetto.jset')
        jetto_namelist = namelist.read(source_drc / 'jetto.in')

        jetto_sanco = None
        if (source_drc / 'jetto.sin').exists():
            jetto_sanco = namelist.read(source_drc / 'jetto.sin')

        all_files = os.listdir(source_drc)

        jetto_extra: List[str] = []
        for regex in _EXTRA_FILE_REGEXES:
            jetto_extra = jetto_extra + list(filter(regex.match, all_files))

        jetto_extra = [str(source_drc / file) for file in jetto_extra]

        jetto_template = template.Template(jset=jetto_jset,
                                           namelist=jetto_namelist,
                                           lookup=jetto_lookup,
                                           sanco_namelist=jetto_sanco,
                                           extra_files=jetto_extra)

        JettoSystem._apply_patches_to_template(jetto_template)

        jetto_config = config.RunConfig(jetto_template)

        jetto_config.export(target_drc)
        lookup.to_file(jetto_lookup, target_drc /
                       'lookup.json')  # TODO, this should be copied as well

        for filename in (
                'rjettov',
                'utils_jetto',
        ):
            src = source_drc / filename
            dst = target_drc / filename
            shutil.copyfile(src, dst)
            dst.chmod(dst.stat().st_mode | stat.S_IXUSR)

    @staticmethod
    def imas_from_path(template_drc: Path) -> ImasHandle:
        jetto_jset = jset.read(template_drc / 'jetto.jset')

        return ImasHandle(
            db=jetto_jset['SetUpPanel.idsIMASDBMachine'],  # type: ignore
            user=jetto_jset['SetUpPanel.idsIMASDBUser'],  # type: ignore
            run=jetto_jset['SetUpPanel.idsIMASDBRunid'],  # type: ignore
            shot=jetto_jset['SetUpPanel.idsIMASDBShot'])  # type: ignore

    @staticmethod
    @add_to_op_queue('Updating imas locations of', '{run}', quiet=True)
    def update_imas_locations(run: Path, inp: ImasHandle, out: ImasHandle):
        jetto_template = template.from_directory(run)
        jetto_config = config.RunConfig(jetto_template)

        jetto_config['user_in'] = inp.user
        jetto_config['machine_in'] = inp.db
        jetto_config['shot_in'] = inp.shot
        jetto_config['run_in'] = inp.run

        jetto_config['machine_out'] = out.db
        jetto_config['shot_out'] = out.shot
        jetto_config['run_out'] = out.run

        jetto_config.export(run)  # Just overwrite the poor files

    @staticmethod
    def set_jetto_variable(run: Path,
                           key: str,
                           value,
                           variable: Optional[JettoVar] = None):
        jetto_template = template.from_directory(run)

        if variable:
            extra_lookup = lookup.from_json(jettovar_to_json(variable))
            jetto_template._lookup.update(extra_lookup)

        jetto_config = config.RunConfig(jetto_template)

        if key == 't_start':
            jetto_config.start_time = value
        elif key == 't_end':
            jetto_config.end_time = value
        else:
            jetto_config[key] = value

        jetto_config.export(run)  # Just overwrite the poor files


class JettoSystemV210921(BaseJettoSystem):

    @staticmethod
    def get_data_in_handle(
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

    @staticmethod
    def get_data_out_handle(
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


class JettoSystemV220922(BaseJettoSystem):

    @staticmethod
    def get_data_in_handle(
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ):
        """Get handle for data input."""
        return ImasHandle(
            user=str((dirname / 'imasdb').resolve()),
            db=source.db,
            shot=source.shot,
            run=1,
        )

    @staticmethod
    def get_data_out_handle(
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ):
        """Get handle for data output."""
        return ImasHandle(
            user=str((dirname / 'imasdb').resolve()),
            db=source.db,
            shot=source.shot,
            run=2,
        )


JettoSystem = JettoSystemV220922
