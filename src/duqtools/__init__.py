# https://setuptools.pypa.io/en/latest/pkg_resources.html#workingset-objects
def fix_dependencies():
    import __main__
    __main__.__requires__ = ['jetto_tools>=1.8.6']
    import pkg_resources  # noqa


fix_dependencies()

__author__ = 'Carbon Collective'
__email__ = 's.smeets@esciencecenter.nl'
__version__ = '1.1.0'

import logging  # noqa
import warnings  # noqa

logging.basicConfig(level=logging.INFO)

# https://github.com/duqtools/duqtools/issues/264
warnings.filterwarnings(
    'ignore',
    'Explicit custom root behavior not yet implemented for pydantic_yaml')
