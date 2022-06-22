import logging
from pathlib import Path

import yaml

import duqtools.config

from .basemodel import BaseModel

logger = logging.getLogger(__name__)


def init(config: str = 'config.yaml', force: bool = False, **kwargs):
    """Initialize a brand new config file with all the default values.

    Parameters
    ----------
    config : str
        Filename of the config.
    force : bool
        Overwrite config if it already exists.
    kwargs :
        kwargs, optional stuff.
    """
    cfg = duqtools.config.Config()

    BaseModel.__init__(cfg)

    logger.debug(cfg)

    config_filepath = Path(config)

    if config_filepath.exists() and not force:
        raise RuntimeError('Refusing to overwrite existing CONFIG, %s \
                    , use --force if you really want to' % config_filepath)

    logger.info('Writing default config to %s' % config_filepath)

    with open(config_filepath, 'w') as f:
        f.write(yaml.dump(yaml.safe_load(cfg.json())))
