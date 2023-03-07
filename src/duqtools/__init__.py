# https://setuptools.pypa.io/en/latest/pkg_resources.html#workingset-objects
def fix_dependencies():
    import __main__
    __main__.__requires__ = ['jetto_tools>=1.8.8']
    __main__.__requires__ = ['jinja2>=3.0.0']
    import pkg_resources  # noqa


fix_dependencies()

__author__ = 'Stef Smeets'
__email__ = 's.smeets@esciencecenter.nl'
__version__ = '1.5.0'

import logging  # noqa
import warnings  # noqa

logging.basicConfig(level=logging.INFO)

# https://github.com/duqtools/duqtools/issues/264
warnings.filterwarnings(
    'ignore',
    'Explicit custom root behavior not yet implemented for pydantic_yaml')
