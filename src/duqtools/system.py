from pathlib import Path

from .config import Config, cfg
from .ids import ImasHandle
from .jetto import JettoSystemV210921, JettoSystemV220922
from .models import AbstractSystem, Job


class DummySystem(AbstractSystem):
    """This is a dummy system that implements the basic interfaces.

    It exists for testing purposes in absence of actual modelling
    software.
    """

    @staticmethod
    def get_runs_dir() -> Path:
        return Path()

    @staticmethod
    def write_batchfile(run_dir: Path, cfg: Config):
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
    def update_imas_locations(run: Path, inp, out):
        pass


def get_system():
    """get_system.

    Get the system to do operations with TODO make it a variable, not a
    function
    """
    if (cfg.system in ['jetto', 'jetto-v220922']):
        return JettoSystemV220922
    elif (cfg.system in ['jetto-v210921']):
        return JettoSystemV210921
    elif (cfg.system == 'dummy'):
        return DummySystem
    else:
        raise NotImplementedError(f'system {cfg.system} is not implemented')
