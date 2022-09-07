import logging
from pathlib import Path

from .config import Config
from .operations import op_queue
from .schema import BaseModel, OperationDim

logger = logging.getLogger(__name__)


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
    cfg = object.__new__(Config)
    BaseModel.__init__(cfg)

    cfg.create.dimensions = [
        OperationDim(variable='t_i_average'),
        OperationDim(variable='zeff'),
        OperationDim(variable='major_radius',
                     values=[296, 297],
                     operator='copyto')
    ]

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
                'variables': True,
                'create': {'dimensions', 'sampler', 'template', 'data'},
                'quiet': False,
            })

    op_queue.add(action=lambda: open(config_filepath, 'w').write(cfg_yaml),
                 description='Writing out',
                 extra_description=f'{config_filepath} config file')
