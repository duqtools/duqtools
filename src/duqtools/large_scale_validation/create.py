from pathlib import Path

from ..config import cfg
from ..create import create as duqtools_create
from ..utils import read_imas_handles_from_file, work_directory


def create(*, base: bool, input_file: str, pattern: str, **kwargs):
    """Create runs for large scale validation.

    Parameters
    ----------
    base : bool
        If true, create base runs by ignoring `sampler`/`dimensions`.
    input_file : str
        Only create for configs where template_data matches a handle in the data.csv
    pattern : str
        Find runs.yaml files only in subdirectories matching this glob pattern
    """
    if pattern is None:
        pattern = '**'

    handles = None
    if input_file:
        handles = read_imas_handles_from_file(input_file).values()

    cwd = Path.cwd()

    config_files = cwd.glob(f'{pattern}/duqtools.yaml')

    for config_file in config_files:
        cfg.parse_file(config_file)

        if handles and (cfg.create.template_data not in handles):
            continue

        config_dir = config_file.parent

        with work_directory(config_dir):
            duqtools_create(config=config_file,
                            absolute_dirpath=True,
                            base=base,
                            **kwargs)
