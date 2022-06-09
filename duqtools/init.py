from logging import debug, error, info
from pathlib import Path

import yaml

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
    debug(cfg)
    config_filepath = Path(args.CONFIG)
    if config_filepath.exists() and not args.force:
        error('Refusing to overwrite existing CONFIG, %s \
                    , use --force if you really want to' % config_filepath)
        return
    info('Writing default config to %s' % config_filepath)
    with open(config_filepath, 'w') as f:
        f.write(yaml.dump(yaml.safe_load(cfg.json())))
