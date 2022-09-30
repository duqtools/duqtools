import logging
import shutil
from pathlib import Path

from importlib_resources import files

from .operations import op_queue

logger = logging.getLogger(__name__)


def init(*, config: str, force: bool, **kwargs):
    """Initialize a brand new config file with all the default values.

    Parameters
    ----------
    config : str
        Filename of the config.
    force : bool
        Overwrite config if it already exists.
    **kwargs
        Unused.

    Raises
    ------
    RuntimeError
        When the config already exists.
    """
    src = files('duqtools.data') / 'duqtools.yaml'

    config_filepath = Path(config)

    if config_filepath.exists() and not force:
        raise RuntimeError(
            f'Refusing to overwrite existing CONFIG, {config_filepath}, '
            'use --force if you really want to')

    logger.debug('Copying default config from %s to %s', src, config_filepath)

    op_queue.add(action=shutil.copy,
                 kwargs={
                     'src': src,
                     'dst': config_filepath,
                 },
                 description='Copying config to',
                 extra_description=f'{config_filepath}')
