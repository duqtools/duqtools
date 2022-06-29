import logging
from pathlib import Path

from duqtools.config import Config

from .config.basemodel import BaseModel

logger = logging.getLogger(__name__)


def init(config: str = 'config.yaml',
         full: bool = False,
         force: bool = False,
         **kwargs):
    """Initialize a brand new config file with all the default values.

    Parameters
    ----------
    config : str
        Filename of the config.
    force : bool
        Overwrite config if it already exists.
    full : bool
        Make a config with all the default values
        (otherwise just selected important ones)
    kwargs :
        kwargs, optional stuff.
    """
    cfg = Config()
    BaseModel.__init__(cfg)

    logger.debug(cfg)

    config_filepath = Path(config)

    if config_filepath.exists() and not force:
        raise RuntimeError(
            'Refusing to overwrite existing CONFIG, {config_filepath}, '
            'use --force if you really want to')

    logger.info('Writing default config to %s', config_filepath)

    if full:
        cfg_yaml = cfg.yaml(descriptions=True)
    else:
        cfg_yaml = cfg.yaml(descriptions=True,
                            include={
                                'workspace': True,
                                'create': {'matrix', 'sampler', 'template'},
                                'plot': {'plots'}
                            })

    with open(config_filepath, 'w') as f:
        f.write(cfg_yaml)
