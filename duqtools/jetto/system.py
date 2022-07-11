from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from typing_extensions import Literal

from ..config.basemodel import BaseModel
from ..config.system import AbstractSystem
from ._imas_functions import imas_from_jset_input
from ._jset import JettoSettings

if TYPE_CHECKING:
    from ..config import Run, WorkDirectory
    from ..config.imaslocation import ImasLocation


class JettoSystem(BaseModel, AbstractSystem):
    name: Literal['jetto'] = 'jetto'

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
    def update_imas_locations(run: Path, inp: ImasLocation, out: ImasLocation):
        jset = JettoSettings.from_directory(run)
        jset_copy = jset.set_imas_locations(inp=inp, out=out)
        jset_copy.to_directory(run)
