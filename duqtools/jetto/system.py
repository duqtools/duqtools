from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import Field
from typing_extensions import Literal

from ..config.system import AbstractSystem
from ._imas_functions import imas_from_jset_input
from ._jset import JettoSettings

if TYPE_CHECKING:
    from ..config import Run, WorkDirectory
    from ..ids.handler import ImasHandle


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
    def write_batchfile(workspace: WorkDirectory, run_name: str):
        from duqtools.jetto import write_batchfile as jetto_write_batchfile
        return jetto_write_batchfile(workspace, run_name)

    @staticmethod
    def get_imas_location(run: Run):
        return run.data_out

    @staticmethod
    def copy_from_template(source_drc: Path, target_drc: Path):
        from duqtools.jetto import copy_files
        return copy_files(source_drc, target_drc)

    @staticmethod
    def imas_from_path(template_drc: Path):

        jset = JettoSettings.from_directory(template_drc)
        source = imas_from_jset_input(jset)
        assert source.path().exists()
        return source

    @staticmethod
    def update_imas_locations(run: Path, inp: ImasHandle, out: ImasHandle):
        jset = JettoSettings.from_directory(run)
        jset_copy = jset.set_imas_locations(inp=inp, out=out)
        jset_copy.to_directory(run)
