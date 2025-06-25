from __future__ import annotations

import logging
import os
import shutil
import stat
import subprocess as sp
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional

from jetto_tools import config, jset, lookup, namelist, template
from jetto_tools import job as jetto_job
from jetto_tools.template import _EXTRA_FILE_REGEXES

from duqtools.operations import add_to_op_queue

from ..base_system import AbstractSystem
from ..jintrac import V220922Mixin
from ._batchfile import write_array_batchfile as _write_array_batchfile
from ._batchfile import write_batchfile as _write_batchfile
from ._jettovar_to_json import jettovar_to_json

if TYPE_CHECKING:
    from types import SimpleNamespace

    from duqtools.api import ImasHandle, Job

    from ..schema import JettoVar, JettoVariableModel
    from ._schema import JettoSystemModel
    from .dimensions import JettoOperation

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files

logger = logging.getLogger(__name__)

# https://jintrac.gitlab.io/jetto-pythontools/lookup.html
lookup_file = os.environ.get('JETTO_LOOKUP',
                             files('duqtools.data') / 'jetto_lookup.json')
jetto_lookup = lookup.from_file(lookup_file)


def _get_jetto_extra(filenames: List[str], *, jset):
    jetto_extra: List[str] = []
    for regex in _EXTRA_FILE_REGEXES:
        jetto_extra.extend(filter(regex.match, filenames))

    if not jset.restart:
        for fname in ('jetto.restart', 'jetto.srestart'):
            try:
                jetto_extra.remove(fname)
            except ValueError:
                pass
    else:
        if 'jetto.restart' in jetto_extra or 'jetto.srestart' in jetto_extra:
            raise OSError(
                'Template contains `jetto.restart` and/or `jetto.srestart` files. '
                'Please remove these or turn "restart off" in JAMS'
                'before running duqtools again.'
                'More info: https://github.com/duqtools/duqtools/issues/498')

    return { file: file for file in jetto_extra }


class BaseJettoSystem(AbstractSystem):
    """System that can be used to create runs for jetto.

    This system can submit to various backends like docker, prominence
    and the gateway.
    """
    options: JettoSystemModel

    @property
    def jruns_path(self) -> Path:
        """Return the Path specified in the system>jruns config variable, or,
        if that is empty, the `$JRUNS` environment variable, or, if `$JRUNS`
        does not exists, return the current directory `./`.

        Returns
        -------
        Path
        """
        if self.options.jruns:
            return Path(self.options.jruns)
        elif jruns_env := os.getenv('JRUNS'):
            return Path(jruns_env)
        else:
            return Path()

    def get_runs_dir(self) -> Path:
        path = self.jruns_path

        assert self.cfg.create
        runs_dir = self.cfg.create.runs_dir

        if runs_dir:
            return path / runs_dir

        abs_cwd = str(Path.cwd().resolve())
        abs_jruns = str(path.resolve())

        # Check if jruns is parent dir of current dir
        if abs_cwd.startswith(abs_jruns):
            return path

        count = 0
        while True:  # find the next free folder
            dirname = f'duqtools_experiment_{count:04d}'
            if not (path / dirname).exists():
                break
            count = count + 1

        return path / dirname

    @add_to_op_queue('Writing new batchfile', '{run_dir.name}', quiet=True)
    def write_batchfile(self, run_dir: Path):
        jetto_jset = jset.read(run_dir / 'jetto.jset')
        _write_batchfile(run_dir,
                         jetto_jset,
                         cfg=self.cfg,
                         jruns_path=self.jruns_path)

    def submit_job(self, job: Job):
        # Make sure we get a new correct status
        if (job.path / 'jetto.status').exists():
            os.remove(job.path / 'jetto.status')

        submit_system = self.options.submit_system

        if submit_system == 'slurm':
            submit = self.submit_slurm
        elif submit_system == 'docker':
            submit = self.submit_docker
        elif submit_system == 'prominence':
            submit = self.submit_prominence
        else:
            raise NotImplementedError(f'submission type {submit_system}'
                                      ' not implemented')

        submit(job)

    def submit_slurm(self, job: Job):
        jetto_template = template.from_directory(job.path)
        jetto_config = config.RunConfig(jetto_template)
        jetto_manager = jetto_job.JobManager()

        logger.info(f'submitting script via slurm')
        rundir = job.path / "rundir"
        rundir = os.path.relpath(rundir, self.jruns_path)
        breakpoint()
        jetto_manager.submit_job_to_batch(config = jetto_config, rundir = rundir)

        with open(job.lockfile, 'wb') as f:
            f.write("submitted")

    def submit_docker(self, job: Job):
        jetto_template = template.from_directory(job.path)
        jetto_config = config.RunConfig(jetto_template)
        jetto_manager = jetto_job.JobManager()
        extra_volumes = {
            job.path.parent / 'imasdb': {
                'bind': '/opt/imas/shared/imasdb',
                'mode': 'rw'
            },
        }

        os.environ['RUNS_HOME'] = os.getcwd()
        container = jetto_manager.submit_job_to_docker(
            jetto_config,
            job.path,
            image=self.options.docker_image,
            extra_volumes=extra_volumes)
        job.lockfile.touch()
        with open(job.lockfile, 'w') as f:
            f.write(container.name)

    def submit_prominence(self, job: Job):
        jetto_template = template.from_directory(job.path)
        config.RunConfig(jetto_template)
        jetto_job.JobManager()
        jetto_jset = jset.read(job.path / 'jetto.jset')

        # Jetto tools decided to be weird, so we use jams/prom-submit.py
        cmd = [
            'prom-submit.py', '--rundir',
            str(job.path), '--image', self.options.prominence_image, '--cpus',
            str(jetto_jset['JobProcessingPanel.numProcessors']), '--walltime',
            '24.0', '--name', f'duqtools_{job.path.name}', '--cmd',
            '/docker-entrypoint.sh rjettov -I -xmpi -x64'
        ]

        ret = sp.run(cmd, check=True, capture_output=True)
        with open(job.lockfile, 'wb') as f:
            f.write(ret.stdout)

    def submit_array(
        self,
        jobs: Sequence[Job],
        *,
        max_jobs: int = 10,
        max_array_size: int = 100,
        create_only=False,
        **kwargs,
    ):
        if self.options.submit_system == 'slurm':
            self.create_array_slurm(jobs,
                                    max_jobs=max_jobs,
                                    max_array_size=max_array_size)
            if not create_only:
                self.submit_array_slurm(jobs)

        else:
            raise NotImplementedError(
                f'array submission type {self.options.submit_system}'
                ' not implemented')

    @add_to_op_queue('Create array job',
                     'Submit using `sbatch duqtools_slurm_array.sh`')
    def create_array_slurm(
        self,
        jobs: Sequence[Job],
        max_jobs: int,
        max_array_size: int,
        **kwargs,
    ):
        logger.info('writing duqtools_slurm_array.sh file')
        _write_array_batchfile(jobs, max_jobs, max_array_size)

    @add_to_op_queue('Submit array job', 'duqtools_slurm_array.sh')
    def submit_array_slurm(
        self,
        jobs: Sequence[Job],
        **kwargs,
    ):
        for job in jobs:
            job.lockfile.touch()

        submit_cmd = self.options.submit_command.split()
        cmd: list[Any] = [*submit_cmd, 'duqtools_slurm_array.sh']

        logger.info(f'Submitting script via: {cmd}')

        ret = sp.run(cmd, check=True, capture_output=True)
        logger.info('submission returned: ' + str(ret.stdout))

        for job in jobs:
            with open(job.lockfile, 'wb') as f:
                f.write(ret.stdout)

    def _apply_patches_to_template(self, jetto_template: template.Template):
        """Apply settings that are necessary for duqtools to function."""
        # Force output of IDS data
        # https://github.com/duqtools/duqtools/issues/343
        jetto_template.jset._settings['JobProcessingPanel.selIdsRunid'] = True

    @add_to_op_queue('Copying template to', '{target_drc}', quiet=True)
    def copy_from_template(self, source_drc: Path, target_drc: Path):

        jetto_jset = jset.read(source_drc / 'jetto.jset')
        jetto_namelist = namelist.read(source_drc / 'jetto.in')

        jetto_sanco = None
        if (source_drc / 'jetto.sin').exists():
            jetto_sanco = namelist.read(source_drc / 'jetto.sin')

        all_files = os.listdir(source_drc)

        jetto_extra = _get_jetto_extra(all_files, jset=jetto_jset)

        jetto_extra = {file : str(source_drc / val) for file, val in jetto_extra.items()}

        jetto_template = template.Template(jset=jetto_jset,
                                           namelist=jetto_namelist,
                                           lookup=jetto_lookup,
                                           sanco_namelist=jetto_sanco,
                                           extra_files=jetto_extra)

        self._apply_patches_to_template(jetto_template)

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

    def imas_from_path(self, template_drc: Path) -> ImasHandle:
        from duqtools.api import ImasHandle

        jetto_jset = jset.read(template_drc / 'jetto.jset')

        return ImasHandle(
            db=jetto_jset['SetUpPanel.idsIMASDBMachine'],  # type: ignore
            user=jetto_jset['SetUpPanel.idsIMASDBUser'],  # type: ignore
            run=jetto_jset['SetUpPanel.idsIMASDBRunid'],  # type: ignore
            shot=jetto_jset['SetUpPanel.idsIMASDBShot'])  # type: ignore

    @add_to_op_queue('Updating imas locations of', '{run}', quiet=True)
    def update_imas_locations(
        self,
        run: Path,
        inp: ImasHandle,
        out: ImasHandle,
        **kwargs,
    ):
        jetto_template = template.from_directory(run)
        jetto_config = config.RunConfig(jetto_template)

        jetto_config['user_in'] = inp.user
        jetto_config['machine_in'] = inp.db
        jetto_config['shot_in'] = inp.shot
        jetto_config['run_in'] = inp.run

        jetto_config['machine_out'] = out.db
        jetto_config['shot_out'] = out.shot
        #jetto_config['run_out'] = out.run

        jetto_config.export(run)  # Just overwrite the poor files

    def get_variable(self, run: Path, key: str, variable: JettoVariableModel):
        jetto_template = template.from_directory(run)
        extra_lookup = lookup.from_json(jettovar_to_json(variable.lookup))
        jetto_template._lookup.update(extra_lookup)
        jetto_config = config.RunConfig(jetto_template)
        return jetto_config[key]

    def set_jetto_variable(self,
                           run: Path,
                           key: str,
                           value,
                           variable: Optional[JettoVar] = None,
                           operation: Optional[JettoOperation] = None,
                           input_var: Optional[SimpleNamespace] = None,
                           **kwargs):
        jetto_template = template.from_directory(run)

        if variable:
            extra_lookup = lookup.from_json(jettovar_to_json(variable))
            jetto_template._lookup.update(extra_lookup)

        jetto_config = config.RunConfig(jetto_template)

        special_keys = (
            't_start',
            't_end',
        )

        # Do operation if present
        if key not in special_keys and operation is not None:
            data = jetto_config[key]
            value = operation.npfunc(data, value, var=input_var)

        if key == 't_start':
            jetto_config.start_time = value
        elif key == 't_end':
            jetto_config.end_time = value
        else:
            jetto_config[key] = value

        jetto_config.export(run)  # Just overwrite the poor files


class JettoSystemV220922(V220922Mixin, BaseJettoSystem):
    """This is the default jetto system that can be used to create runs for
    jetto using the JINTRAC `v220922` release or newer.

    The most important difference with `jetto-v210921` is that the IMAS data are handled locally
    instead of via a public `imasdb`.

    This system can submit to various backends like docker, prominence
    and the gateway.

    ```yaml title="duqtools.yaml"
    system:
      name: jetto-v220922
      submit_system: docker
    ```
    """


JettoSystem = JettoSystemV220922
