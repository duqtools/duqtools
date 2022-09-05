from pathlib import Path

from .config import cfg
from .ids import ImasHandle
from .jettoduqtools import JettoDuqtoolsSystem
from .jettopythontools import JettoPythonToolsSystem
from .models import AbstractSystem, Job, WorkDirectory


class DummySystem(AbstractSystem):
    """This is a dummy system that implements the basic interfaces.

    It exists for testing purposes in absence of actual modelling
    software.
    """

    @staticmethod
    def write_batchfile(workspace: WorkDirectory, run_name: str,
                        template_drc: Path):
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

    @staticmethod
    def set_jetto_variable(run: Path, key: str, value):
        pass


def get_system():
    """get_system.

    Get the system to do operations with TODO make it a variable, not a
    function
    """
    if (cfg.system in ['jetto', 'jetto-duqtools']):
        return JettoDuqtoolsSystem
    elif (cfg.system in ['jetto-pythontools']):
        return JettoPythonToolsSystem
    elif (cfg.system == 'dummy'):
        return DummySystem
    else:
        raise NotImplementedError(f'system {cfg.system} is not implemented')
