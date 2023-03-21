from pathlib import Path

from ..config import cfg
from ..create import create as duqtools_create
from ..utils import work_directory


def create(**kwargs):
    cwd = Path.cwd()

    config_files = cwd.glob('**/duqtools.yaml')

    for config_file in config_files:
        cfg.parse_file(config_file)

        config_dir = config_file.parent

        with work_directory(config_dir):
            duqtools_create(config=config_file,
                            absolute_dirpath=True,
                            **kwargs)
