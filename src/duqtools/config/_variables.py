from __future__ import annotations

import sys

from duqtools.imas2xarray import VariableConfigLoader

from ._models import DuqtoolsVariableConfigModel

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files


class DuqtoolsVariableConfigLoader(VariableConfigLoader):
    MODEL = DuqtoolsVariableConfigModel
    VAR_DIR = 'duqtools'
    VAR_ENV = 'DUQTOOLS_VARDEF'
    MODULE = files('duqtools.data')


var_lookup = DuqtoolsVariableConfigLoader().load()
