from __future__ import annotations

from pathlib import Path

from pydantic import Field
from typing_extensions import Literal

from ..ids import ImasHandle
from ..models import AbstractSystem, WorkDirectory
from ..operations import add_to_op_queue


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
        pass

    @staticmethod
    @add_to_op_queue('Copying template to', '{target_drc}', quiet=True)
    def copy_from_template(source_drc: Path, target_drc: Path):
        pass

    @staticmethod
    def imas_from_path(template_drc: Path):
        return ImasHandle(db='', shot='-1', run='-1')

    @staticmethod
    @add_to_op_queue('Updating imas locations of', '{run}', quiet=True)
    def update_imas_locations(run: Path, inp: ImasHandle, out: ImasHandle):
        pass
