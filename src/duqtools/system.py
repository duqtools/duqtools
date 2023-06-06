from pathlib import Path
from typing import Any

from .config import Config
from .ets import Ets6System
from .ids import ImasHandle
from .jetto import JettoSystemV210921, JettoSystemV220922
from .models import AbstractSystem, Job
from .schema import DummySystemModel


class DummySystem(AbstractSystem, DummySystemModel):
    """This is a dummy system that implements the basic interfaces.

    It exists for testing purposes in absence of actual modelling
    software.
    """

    @staticmethod
    def get_runs_dir() -> Path:
        return Path()

    @staticmethod
    def write_batchfile(run_dir: Path):
        pass

    @staticmethod
    def submit_job(job: Job):
        pass

    @staticmethod
    def copy_from_template(source_drc: Path, target_drc: Path):
        pass

    @staticmethod
    def imas_from_path(template_drc: Path):
        return ImasHandle(db='', shot='-1', run='-1')

    @staticmethod
    def update_imas_locations(run: Path, inp, out, **kwargs):
        pass


def get_system(cfg: Config) -> AbstractSystem:
    """Get the system to do operations with."""
    System: Any = None  # Shut up mypy

    if (cfg.system.name in ['jetto', 'jetto-v220922', 'jetto-v230123']):
        System = JettoSystemV220922
    elif (cfg.system.name in ['jetto-v210921']):
        System = JettoSystemV210921
    elif (cfg.system.name == 'ets6'):
        System = Ets6System
    elif (cfg.system.name == 'dummy'):
        System = DummySystem
    else:
        raise NotImplementedError(
            f'system {cfg.system.name} is not implemented')
    return System.parse_obj({'cfg': cfg, **cfg.system.dict()})
