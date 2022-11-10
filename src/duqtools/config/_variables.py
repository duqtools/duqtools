from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import List, Sequence, Union

from ..schema import IDSVariableModel
from ..schema.variables import VariableConfigModel

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files

logger = logging.getLogger(__name__)

VAR_ENV = 'DUQTOOLS_VARDEF'
USER_CONFIG_HOME = Path.home() / '.config'
LOCAL_DIR = Path('.').absolute()
DUQTOOLS_DIR = 'duqtools'
VAR_FILENAME = 'variables.yaml'


class VariableConfigLoader:

    def __init__(self):
        path = self.get_config_path()

        if not path.exists():
            raise OSError(f'{path} does not exist!')

        self.path = path

    def load(self):
        """Load the variables config."""
        logger.debug(f'Loading variables from: {self.path}')
        return VariableConfigModel.parse_file(self.path)

    def get_config_path(self) -> Path:
        """Try to get the config file with variable definitions.

        Search order:
        1. environment variable
        (2. local directory, not sure if this should be implemented)
        3. config home (first $XDG_CONFIG_HOME/duqtools then `$HOME/.config/duqtools`)
        4. fall back to variable definitions in package
        """
        for path in (
                self._get_path_from_environment_variable(),
                self._get_path_from_config_home(),
                self._get_path_local_directory(),
        ):
            if path:
                return path

        return self._get_path_fallback()

    def _get_path_from_environment_variable(self):
        env = os.environ.get(VAR_ENV)
        if env:
            test_path = Path(env)
            if not test_path.exists():
                raise OSError(
                    f'{test_path} defined by ${VAR_ENV} does not exist!')
            return test_path

    def _get_path_local_directory(self):
        return None  # Not implemented

    def _get_path_from_config_home(self):
        config_home = os.environ.get('XDG_CONFIG_HOME', USER_CONFIG_HOME)

        test_path = Path(config_home) / DUQTOOLS_DIR / VAR_FILENAME
        if test_path.exists():
            return test_path

    def _get_path_fallback(self):
        return files('duqtools.data') / VAR_FILENAME


def lookup_vars(
    variables: Sequence[Union[str,
                              IDSVariableModel]]) -> List[IDSVariableModel]:
    """Helper function to look up a bunch of variables.

    If str, look up the variable from the `var_lookup` Else check if the
    variable is an `IDSVariableModel`
    """
    var_models = []
    for var in variables:
        if isinstance(var, str):
            var = var_lookup[var]
        if not isinstance(var, IDSVariableModel):
            raise ValueError(f'Cannot lookup variable with type {type(var)}')
        var_models.append(var)
    return var_models


variable_config = VariableConfigLoader().load()
var_lookup = variable_config.to_variable_dict()
