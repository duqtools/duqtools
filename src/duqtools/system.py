from pathlib import Path
from warnings import warn

from .config import cfg
from .ids import ImasHandle
from .jetto import JettoSystem
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
    def update_imas_locations(run: Path, inp, out):
        pass


def get_system():
    """get_system.

    Get the system to do operations with TODO make it a variable, not a
    function
    """
    if (cfg.system in ['jetto-pythontools', 'jetto-duqtools']):
        warn(f"{cfg.system} system deprecated, please use 'jetto'",
             DeprecationWarning)

    if (cfg.system in ['jetto', 'jetto-duqtools', 'jetto-pythontools']):
        return JettoSystem
    elif (cfg.system == 'dummy'):
        return DummySystem
    else:
        raise NotImplementedError(f'system {cfg.system} is not implemented')
