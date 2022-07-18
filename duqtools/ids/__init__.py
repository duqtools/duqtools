import logging

import ruamel.yaml as yaml

from .._types import PathLike
from ._get_ids_tree import get_ids_tree
from ._mapping import IDSMapping

logger = logging.getLogger(__name__)


def write_ids(filename: PathLike, data: dict):
    """Write ids data to yaml file [PROOF OF CONCEPT].

    Parameters
    ----------
    filename : PathLike
        Filename to save data to.
    data : dict
        Dictionary with keys to write.
    """
    ruamel_obj = yaml.YAML(typ='safe', pure=True)
    with open(filename, 'w') as f:
        ruamel_obj.dump(data, stream=f)
    logger.debug('wrote %r', filename)


__all__ = [
    'get_ids_tree',
    'IDSMapping',
]
