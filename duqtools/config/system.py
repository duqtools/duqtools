from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import Field
from typing_extensions import Literal

from .basemodel import BaseModel

if TYPE_CHECKING:
    from pathlib import Path

    from ._runs import Run
    from ._workdir import WorkDirectory
    from .imaslocation import ImasLocation

logger = logging.getLogger(__name__)


class AbstractSystem(ABC, BaseModel):

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


class DummySystem(AbstractSystem):
    """Dummy system."""

    name: Literal['dummy'] = Field('dummy', description='Name of the system.')

    @staticmethod
    def write_batchfile(workspace: WorkDirectory, run_name: str):
        pass

    @staticmethod
    def get_imas_location(run: Run):
        pass

    @staticmethod
    def copy_from_template(source_drc: Path, target_drc: Path):
        pass

    @staticmethod
    def imas_from_path(template_drc: Path):
        pass

    @staticmethod
    def update_imas_locations(run: Path, inp: ImasLocation, out: ImasLocation):
        pass
