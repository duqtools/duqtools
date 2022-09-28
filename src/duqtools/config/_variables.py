from __future__ import annotations

import os
from pathlib import Path

from importlib_resources import files

from ..schema.variables import VariableConfigModel

VAR_ENV = 'DUQTOOLS_VARDEF'
USER_CONFIG_HOME = Path.home() / '.config'
LOCAL_DIR = Path('.').absolute()
DUQTOOLS_DIR = 'duqtools'
VAR_FILENAME = 'variables.yaml'


class VariableConfigLoader:

    def __init__(self):
        config_file = self.get_config_file()

        if not config_file.exists():
            raise IOError(f'{config_file} does not exist!')

        self.config_file = config_file

    def load(self):
        """Load the variables config."""
        return VariableConfigModel.parse_file(self.config_file)

    def get_config_file(self) -> Path:
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
                raise IOError(
                    f'{test_path} defined by ${VAR_ENV} does not exist!')
            return test_path

    def _get_path_local_directory(self):
        return None  # Not implemented

    def _get_path_from_config_home(self):
        config_home = os.environ.get('XDG_CONFIG_HOME', USER_CONFIG_HOME)

        test_path = config_home / DUQTOOLS_DIR / VAR_FILENAME
        if test_path.exists():
            return test_path

    def _get_path_fallback(self):
        return files('duqtools.data') / VAR_FILENAME


variable_config = VariableConfigLoader().load()
var_lookup = variable_config.to_variable_dict()
