__author__ = 'Carbon Collective'
__email__ = 's.smeets@esciencecenter.nl'
__version__ = '1.0.0'

import logging
import warnings

logging.basicConfig(level=logging.INFO)

# https://github.com/CarbonCollective/fusion-dUQtools/issues/264
warnings.filterwarnings(
    'ignore',
    'Explicit custom root behavior not yet implemented for pydantic_yaml')
