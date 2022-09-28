from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import Field
from typing_extensions import Literal

from ..jettosystem import JettoSystem
from ..operations import add_to_op_queue, op_queue
from ..schema import JettoVar
from ._imas_functions import imas_from_jset_input
from ._jetto_jset import JettoJset
from ._llcmd import write_batchfile as jetto_write_batchfile
from ._settings_manager import JettoSettingsManager

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..ids import ImasHandle
    from ..models import WorkDirectory


class JettoDuqtoolsSystem(JettoSystem):
    """This system implements a wrapper around JETTO, which is part of the
    JINTRAC modelling framework for integrated simulation of Tokamaks.

    For more information:

    - G. Cenacchi, A. Taroni, JETTO: A free-boundary plasma transport code,
        JET-IR (1988)
    - M. Romanelli  2014, Plasma and Fusion research 9, 3403023-3403023
    """
    name: Literal['jetto'] = Field('jetto', description='Name of the system.')

    @staticmethod
    @add_to_op_queue('Writing new batchfile', '{run_name}', quiet=True)
    def write_batchfile(workspace: WorkDirectory, run_name: str,
                        template_drc: Path):
        jset = JettoJset.from_directory(template_drc)

        return jetto_write_batchfile(workspace, run_name, jset)

    @staticmethod
    @add_to_op_queue('Copying template to', '{target_drc}', quiet=True)
    def copy_from_template(source_drc: Path, target_drc: Path):
        from ..jettopythontools import JettoPythonToolsSystem
        enabled = op_queue.enabled
        op_queue.enabled = False
        JettoPythonToolsSystem.copy_from_template(source_drc, target_drc)
        op_queue.enabled = enabled

    @staticmethod
    def imas_from_path(template_drc: Path):

        jetto_settings = JettoSettingsManager.from_directory(template_drc)
        source = imas_from_jset_input(jetto_settings)
        return source

    @staticmethod
    @add_to_op_queue('Updating imas locations of', '{run}', quiet=True)
    def update_imas_locations(run: Path, inp: ImasHandle, out: ImasHandle):
        jetto_settings = JettoSettingsManager.from_directory(run)
        jetto_settings_copy = jetto_settings.set_imas_locations(inp=inp,
                                                                out=out)
        jetto_settings_copy.to_directory(run)

    @staticmethod
    def set_jetto_variable(run: Path,
                           key: str,
                           value,
                           lookup: JettoVar = None):
        jetto_settings = JettoSettingsManager.from_directory(run)
        if lookup:
            jetto_settings.add_entry(lookup)
        jetto_settings[key] = value
        jetto_settings.to_directory(run)
