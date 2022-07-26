import logging
from pathlib import Path

from .config import Config
from .operations import confirm_operations, op_queue
from .schema import BaseModel

logger = logging.getLogger(__name__)


@confirm_operations
def init(*, config: str, full: bool, force: bool, **kwargs):
    """Initialize a brand new config file with all the default values.

    Parameters
    ----------
    config : str
        Filename of the config.
    full : bool
        Make a config with all the default values
        (otherwise just selected important ones)
    force : bool
        Overwrite config if it already exists.
    **kwargs
        Unused.

    Raises
    ------
    RuntimeError
        When the config already exists.
    """
    cfg = Config()
    BaseModel.__init__(cfg)

    logger.debug(cfg)

    config_filepath = Path(config)

    if config_filepath.exists() and not force:
        raise RuntimeError(
            f'Refusing to overwrite existing CONFIG, {config_filepath}, '
            'use --force if you really want to')

    logger.debug('Creating default cfg.yaml')

    if full:
        cfg_yaml = cfg.yaml()
    else:
        cfg_yaml = cfg.yaml(
            include={
                'workspace': True,
                'create': {'dimensions', 'sampler', 'template', 'data'},
            })

    op_queue.add(action=lambda: open(config_filepath, 'w').write(cfg_yaml),
                 description='Writing out',
                 extra_description=f'{config_filepath} config file')
