# https://github.com/CarbonCollective/fusion-dUQtools/issues/27

import logging

logger = logging.getLogger(__name__)

try:
    import imas
    from imas import imasdef
except (ModuleNotFoundError, ImportError):
    from unittest.mock import MagicMock as Mock
    imas = Mock()
    imasdef = Mock()

    logger.warning('Could not import IMAS:', exc_info=True)
