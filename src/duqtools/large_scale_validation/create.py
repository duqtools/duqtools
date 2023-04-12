from pathlib import Path

from ..config import cfg
from ..create import create as duqtools_create
from ..utils import work_directory


def create(*, pattern: str = '**', **kwargs):
    """Create runs for large scale validation.

    Parameters
    ----------
    pattern : str
        Find runs.yaml files only in subdirectories matching this glob pattern
    """
    cwd = Path.cwd()

    config_files = cwd.glob(f'{pattern}/duqtools.yaml')

    for config_file in config_files:
        cfg.parse_file(config_file)

        config_dir = config_file.parent

        with work_directory(config_dir):
            duqtools_create(config=config_file,
                            absolute_dirpath=True,
                            **kwargs)
