import logging
from pathlib import Path

import yaml

from ._types import BaseModel
from .config import cfg

logger = logging.getLogger(__name__)


def cleanup(force: bool = False, **kwargs):
    """Read runs.yaml and clean the current directory.

    Parameters
    ----------
    force : bool
        Overwrite config if it already exists.
    kwargs :
        Unused.
    """
    # runs_yaml

    print('hello world')
