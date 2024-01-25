from __future__ import annotations

import sys
from typing import Union

from imas2xarray import VariableConfigLoader, VariableConfigModel

from duqtools.systems.jetto import IDS2JettoVariableModel, JettoVariableModel

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files


class DuqtoolsVariableConfigModel(VariableConfigModel):
    root: list[Union[JettoVariableModel, IDS2JettoVariableModel]]


imas2xarray_var_lookup = VariableConfigLoader().load()

var_lookup = VariableConfigLoader(
    model=DuqtoolsVariableConfigModel,
    var_dir='duqtools',
    var_env='DUQTOOLS_VARDEF',
    module=files('duqtools.data'),
).load(var_lookup=imas2xarray_var_lookup)
