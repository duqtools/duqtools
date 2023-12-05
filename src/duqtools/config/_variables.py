from __future__ import annotations

import sys

from imas2xarray import VariableConfigLoader

from ._models import DuqtoolsVariableConfigModel

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files

imas2xarray_var_lookup = VariableConfigLoader().load()

var_lookup = VariableConfigLoader(
    model=DuqtoolsVariableConfigModel,
    var_dir='duqtools',
    var_env='DUQTOOLS_VARDEF',
    module=files('duqtools.data'),
).load(var_lookup=imas2xarray_var_lookup)
