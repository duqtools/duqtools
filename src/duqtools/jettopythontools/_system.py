from __future__ import annotations

from pathlib import Path

from jetto_tools import config, job, jset, lookup, namelist, template
from pydantic import Field
from typing_extensions import Literal

from ..ids import ImasHandle
from ..models import AbstractSystem, WorkDirectory
from ..operations import add_to_op_queue

jetto_lookup = lookup.from_file(
    Path(__file__).resolve().parent / 'lookup_temp.json')


class JettoPythonToolsSystem(AbstractSystem):
    """This system implements a wrapper around jettopythontools, which is a
    wrapper around jetto, which is part of the JINTRAC modelling framework for
    integrated simulation of Tokamaks.

    For more information:

    - G. Cenacchi, A. Taroni, JETTO: A free-boundary plasma transport code,
        JET-IR (1988)
    - M. Romanelli  2014, Plasma and Fusion research 9, 3403023-3403023
    - https://pypi.org/project/jetto-tools/
    """
    name: Literal['jetto-pythontools'] = Field(
        'jetto-pythontools', description='Name of the system.')

    @staticmethod
    @add_to_op_queue('Writing new batchfile', '{run_name}', quiet=True)
    def write_batchfile(workspace: WorkDirectory, run_name: str,
                        template_drc: Path):
        jetto_template = template.from_directory(workspace.cwd / run_name)
        jetto_config = config.RunConfig(jetto_template)
        jetto_manager = job.JobManager()

        # jetto_job = jetto_manager.submit_job_to_batch(jetto_config, run_name)

        # Do some manual manipulation instead, submit_job_to_batch is too restrictive
        # ( we want to be able to write to directories outside $runs_home )

        jetto_source_dir = jetto_manager._find_jetto_source_dir(jetto_config)
        jetto_manager._export_batchfile(jetto_config, workspace.cwd / run_name)
        jetto_manager._export_rjettov_script(jetto_source_dir,
                                             workspace.cwd / run_name)
        jetto_manager._export_utils_script(jetto_source_dir,
                                           workspace.cwd / run_name)

    @staticmethod
    @add_to_op_queue('Copying template to', '{target_drc}', quiet=True)
    def copy_from_template(source_drc: Path, target_drc: Path):
        jetto_jset = jset.read(source_drc / 'jetto.jset')
        jetto_namelist = namelist.read(source_drc / 'jetto.in')
        jetto_sanco = namelist.read(source_drc /
                                    'jetto.sin')  # required but unused
        jetto_template = template.Template(jetto_jset,
                                           jetto_namelist,
                                           jetto_lookup,
                                           sanco_namelist=jetto_sanco)
        jetto_config = config.RunConfig(jetto_template)

        jetto_config.export(target_drc)
        lookup.to_file(jetto_lookup, target_drc /
                       'lookup.json')  # TODO, this should be copied as well

    @staticmethod
    def imas_from_path(template_drc: Path):
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
