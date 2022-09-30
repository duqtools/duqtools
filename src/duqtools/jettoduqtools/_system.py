from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import Field
from typing_extensions import Literal

from ..jettosystem import JettoSystem
from ..operations import add_to_op_queue
from ..schema import JettoVar
from ._jetto_jset import JettoJset
from ._llcmd import write_batchfile as jetto_write_batchfile

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
    def copy_from_template(source_drc: Path, target_drc: Path):
        from ..jettopythontools import JettoPythonToolsSystem
        JettoPythonToolsSystem.copy_from_template(source_drc, target_drc)

    @staticmethod
    def imas_from_path(template_drc: Path):
        from ..jettopythontools import JettoPythonToolsSystem
        return JettoPythonToolsSystem.imas_from_path(template_drc)

    @staticmethod
    def update_imas_locations(run: Path, inp: ImasHandle, out: ImasHandle):
        from ..jettopythontools import JettoPythonToolsSystem
        return JettoPythonToolsSystem.update_imas_locations(run, inp, out)

    @staticmethod
    def set_jetto_variable(run: Path,
                           key: str,
                           value,
                           lookup: JettoVar = None):
        from ..jettopythontools import JettoPythonToolsSystem
        return JettoPythonToolsSystem.set_jetto_variable(
            run, key, value, lookup)
