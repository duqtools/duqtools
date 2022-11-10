from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import DirectoryPath

from ..schema import BaseModel, ImasBaseModel, JettoVar

if TYPE_CHECKING:
    from pathlib import Path

    from ._job import Job

logger = logging.getLogger(__name__)


class AbstractSystem(ABC, BaseModel):

    @staticmethod
    @abstractmethod
    def get_runs_dir() -> Path:
        pass

    @staticmethod
    @abstractmethod
    def write_batchfile(run_location: DirectoryPath, run_name: str,
                        template_drc: Path):
        pass

    @staticmethod
    @abstractmethod
    def submit_job(job: Job):
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
    def update_imas_locations(run: Path, inp: ImasBaseModel,
                              out: ImasBaseModel):
        pass

    @staticmethod
    @abstractmethod
    def set_jetto_variable(run: Path, key: str, value, variable: JettoVar):
        pass
