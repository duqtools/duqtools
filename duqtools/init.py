from logging import debug, info
from pathlib import Path

import yaml
from pydantic import BaseModel

import duqtools.config


def init(**kwargs):
    """Initialize a brand new config file with all the default values.

    Parameters
    ----------
    kwargs :
        kwargs, optional stuff
    """
    args = kwargs['args']
    cfg = duqtools.config.Config()
    BaseModel.__init__(cfg)
    debug(cfg)
    config_filepath = Path(args.CONFIG)
    if config_filepath.exists() and not args.force:
        raise RuntimeError('Refusing to overwrite existing CONFIG, %s \
                    , use --force if you really want to' % config_filepath)
    info('Writing default config to %s' % config_filepath)
    with open(config_filepath, 'w') as f:
        f.write(yaml.dump(yaml.safe_load(cfg.json())))
