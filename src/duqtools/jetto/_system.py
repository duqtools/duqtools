from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import Field
from typing_extensions import Literal

from ..models import AbstractSystem
from ..operations import add_to_op_queue
from ._imas_functions import imas_from_jset_input
from ._jetto_jset import JettoJset
from ._settings_manager import JettoSettingsManager

if TYPE_CHECKING:
    from ..ids import ImasHandle
    from ..models import WorkDirectory


class JettoSystem(AbstractSystem):
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
        from duqtools.jetto import write_batchfile as jetto_write_batchfile
        jset = JettoJset.from_directory(template_drc)

        return jetto_write_batchfile(workspace, run_name, jset)

    @staticmethod
    @add_to_op_queue('Copying template to', '{target_drc}', quiet=True)
    def copy_from_template(source_drc: Path, target_drc: Path):
        from duqtools.jetto import copy_files
        return copy_files(source_drc, target_drc)

    @staticmethod
    def imas_from_path(template_drc: Path):

        jetto_settings = JettoSettingsManager.from_directory(template_drc)
        source = imas_from_jset_input(jetto_settings)
        assert source.path().exists()
        return source

    @staticmethod
    @add_to_op_queue('Updating imas locations of', '{run}', quiet=True)
    def update_imas_locations(run: Path, inp: ImasHandle, out: ImasHandle):
        jetto_settings = JettoSettingsManager.from_directory(run)
        jetto_settings_copy = jetto_settings.set_imas_locations(inp=inp,
                                                                out=out)
        jetto_settings_copy.to_directory(run)
