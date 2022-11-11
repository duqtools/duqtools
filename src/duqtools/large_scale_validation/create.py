from pathlib import Path

from ..config import cfg
from ..create import create as duqtools_create


def create(**kwargs):
    cwd = Path.cwd()

    config_files = cwd.glob('**/duqtools.yaml')

    for config_file in config_files:
        cfg.parse_file(config_file)

        duqtools_create()
