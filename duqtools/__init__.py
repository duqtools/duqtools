__author__ = 'Carbon Collective'
__email__ = 's.smeets@esciencecenter.nl'
__version__ = '0.0.1'

import logging

from .__main__ import cmdline, create, plot

logging.basicConfig(level=logging.INFO)

__all__ = [
    'create',
    'plot',
    'cmdline',
]
