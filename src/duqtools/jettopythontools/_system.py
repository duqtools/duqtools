from __future__ import annotations

import logging
from pathlib import Path

from jetto_tools import config
from jetto_tools import job as jetto_job
from jetto_tools import jset, lookup, namelist, template
from pydantic import Field
from typing_extensions import Literal

from ..ids import ImasHandle
from ..models import AbstractSystem, Job, WorkDirectory
from ..operations import add_to_op_queue
from ..schema import JettoVar
from ._jettovar_to_json import jettovar_to_json

logger = logging.getLogger(__name__)

jetto_lookup = lookup.from_file(
    Path(__file__).resolve().parent / 'lookup.json')


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
        pass  # Not required, we submit via prominence

    @staticmethod
    @add_to_op_queue('Submitting job', '{job}', quiet=True)
    def submit_job(job: Job):

        jetto_template = template.from_directory(job.dir)
        jetto_config = config.RunConfig(jetto_template)
        jetto_manager = jetto_job.JobManager()

        _ = jetto_manager.submit_job_to_prominence(jetto_config, job.dir)

    @staticmethod
    @add_to_op_queue('Copying template to', '{target_drc}', quiet=True)
    def copy_from_template(source_drc: Path, target_drc: Path):
        jetto_jset = jset.read(source_drc / 'jetto.jset')
        jetto_namelist = namelist.read(source_drc / 'jetto.in')
        jetto_sanco = None
        if (source_drc / 'jetto.sin').exists():
            jetto_sanco = namelist.read(source_drc / 'jetto.sin')
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

    @staticmethod
    def set_jetto_variable(run: Path,
                           key: str,
                           value,
                           variable: JettoVar = None):
        jetto_template = template.from_directory(run)

        if variable:
            extra_lookup = lookup.from_json(jettovar_to_json(variable))
            jetto_template._lookup.update(extra_lookup)

        jetto_config = config.RunConfig(jetto_template)

        jetto_config[key] = value

        jetto_config.export(run)  # Just overwrite the poor files
