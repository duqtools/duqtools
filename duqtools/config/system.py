from abc import ABC, abstractmethod

from typing_extensions import Literal

from duqtools.jetto import write_batchfile as jetto_write_batchfile

from .basemodel import BaseModel
from .workdir import WorkDirectory


class AbstractSystem(ABC):

    @staticmethod
    @abstractmethod
    def write_batchfile(workspace: WorkDirectory, run_name: str):
        pass


class JettoSystem(BaseModel, AbstractSystem):
    name: Literal['jetto'] = 'jetto'

    @staticmethod
    def write_batchfile(workspace: WorkDirectory, run_name: str):
        return jetto_write_batchfile(workspace, run_name)


class DummySystem(BaseModel):
    name: Literal['dummy'] = 'dummy'
