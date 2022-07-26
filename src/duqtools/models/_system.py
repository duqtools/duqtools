from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..schema import BaseModel, ImasBaseModel

if TYPE_CHECKING:
    from pathlib import Path

    from .workdir import WorkDirectory

logger = logging.getLogger(__name__)


class AbstractSystem(ABC, BaseModel):

    @staticmethod
    @abstractmethod
    def write_batchfile(workspace: WorkDirectory, run_name: str):
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
