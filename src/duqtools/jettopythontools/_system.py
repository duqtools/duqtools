from __future__ import annotations

import logging
from pathlib import Path

from importlib_resources import files
from jetto_tools import config, jset, lookup, namelist, template
from pydantic import Field
from typing_extensions import Literal

from ..ids import ImasHandle
from ..jettosystem import JettoSystem
from ..models import WorkDirectory
from ..operations import add_to_op_queue
from ..schema import JettoVar
from ._jettovar_to_json import jettovar_to_json

logger = logging.getLogger(__name__)

lookup_file = files('duqtools.data') / 'jetto_tools_lookup.json'
jetto_lookup = lookup.from_file(lookup_file)


class JettoPythonToolsSystem(JettoSystem):
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
    def write_batchfile(workspace: WorkDirectory, run_name: str,
                        template_drc: Path):
        from ..jettoduqtools import JettoDuqtoolsSystem

        # broken, use our own implementation
        JettoDuqtoolsSystem.write_batchfile(workspace, run_name, template_drc)

    @staticmethod
    @add_to_op_queue('Copying template to', '{target_drc}', quiet=True)
    def copy_from_template(source_drc: Path, target_drc: Path):
        jetto_jset = jset.read(source_drc / 'jetto.jset')
        jetto_namelist = namelist.read(source_drc / 'jetto.in')
        jetto_sanco = None
        jetto_extra = []
        if (source_drc / 'jetto.sin').exists():
            jetto_sanco = namelist.read(source_drc / 'jetto.sin')
        if (source_drc / 'jetto.ex').exists():
            jetto_extra.append(str(source_drc / 'jetto.ex'))

        jetto_template = template.Template(jetto_jset,
                                           jetto_namelist,
                                           jetto_lookup,
                                           sanco_namelist=jetto_sanco,
                                           extra_files=jetto_extra)
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

        if key == 't_start':
            jetto_config.start_time = value
        elif key == 't_end':
            jetto_config.end_time = value
        else:
            jetto_config[key] = value

        jetto_config.export(run)  # Just overwrite the poor files
