from pathlib import Path

from .config import AbstractSystem, Run, WorkDirectory, cfg
from .jetto import JettoSystem


class DummySystem(AbstractSystem):
    """This is a dummy system that implements the basic interfaces.

    It exists for testing purposes in absence of actual modelling
    software.
    """

    @staticmethod
    def write_batchfile(workspace: WorkDirectory, run_name: str):
        pass

    @staticmethod
    def get_imas_location(run: Run):
        return run.data_out

    @staticmethod
    def copy_from_template(source_drc: Path, target_drc: Path):
        pass

    @staticmethod
    def imas_from_path(template_drc: Path):
        raise NotImplementedError('')
        # return ImasLocation(db='', shot='-1', run='-1')

    @staticmethod
    def update_imas_locations(run: Path, inp, out):
        pass


def get_system():
    """get_system.

    Get the system to do operations with TODO make it a variable, not a
    function
    """
    if (cfg.system == 'jetto'):
        return JettoSystem
    elif (cfg.system == 'dummy'):
        return DummySystem
    else:
        raise NotImplementedError(f'system {cfg.system} is not implemented')
