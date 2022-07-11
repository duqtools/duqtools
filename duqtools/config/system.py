import logging
from abc import ABC, abstractmethod
from pathlib import Path

from typing_extensions import Literal

from duqtools.ids._location import ImasLocation
from duqtools.jetto._jset import JettoSettings

from ._runs import Run
from .basemodel import BaseModel
from .workdir import WorkDirectory

logger = logging.getLogger(__name__)


class AbstractSystem(ABC):

    @staticmethod
    @abstractmethod
    def write_batchfile(workspace: WorkDirectory, run_name: str):
        pass

    @staticmethod
    @abstractmethod
    def get_imas_location(run: Run):
        pass

    @staticmethod
    @abstractmethod
    def copy_from_template(source_drc: Path, target_drc: Path):
        pass

    @staticmethod
    @abstractmethod
    def imas_from_path(template_drc: Path):
        pass

    @staticmethod
    @abstractmethod
    def update_imas_locations(run: Path, inp: ImasLocation, out: ImasLocation):
        pass


class JettoSystem(BaseModel, AbstractSystem):
    name: Literal['jetto'] = 'jetto'

    @staticmethod
    def write_batchfile(workspace: WorkDirectory, run_name: str):
        from duqtools.jetto._llcmd import \
            write_batchfile as jetto_write_batchfile
        return jetto_write_batchfile(workspace, run_name)

    @staticmethod
    def get_imas_location(run: Run):
        return run.data_out

    @staticmethod
    def copy_from_template(source_drc: Path, target_drc: Path):
        from duqtools.jetto._copy import copy_files
        return copy_files(source_drc, target_drc)

    @staticmethod
    def imas_from_path(template_drc: Path):

        jset = JettoSettings.from_directory(template_drc)
        source = ImasLocation.from_jset_input(jset)
        assert source.path().exists()
        return source

    @staticmethod
    def update_imas_locations(run: Path, inp: ImasLocation, out: ImasLocation):
        jset = JettoSettings.from_directory(run)
        jset_copy = jset.set_imas_locations(inp=inp, out=out)
        jset_copy.to_directory(run)


class DummySystem(BaseModel):
    name: Literal['dummy'] = 'dummy'
