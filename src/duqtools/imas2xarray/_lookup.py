from __future__ import annotations

import logging
import operator
import os
import sys
from collections import UserDict
from pathlib import Path, PosixPath
from typing import Hashable, Sequence

from pydantic_yaml import parse_yaml_raw_as

from ..utils import groupby
from ._models import IDSVariableModel, VariableConfigModel

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files

logger = logging.getLogger(__name__)

USER_CONFIG_HOME = Path.home() / '.config'
LOCAL_DIR = Path('.').absolute()
VAR_FILENAME = 'variables.yaml'
VAR_FILENAME_GLOB = 'variables*.yaml'
ERROR_SUFFIX = '_error_upper'


class VarLookup(UserDict):
    _prefix = '$'
    """Variable lookup table.

    Subclasses `UserDict` to embed some commonly used operations, like
    grouping and filtering.
    """
    _ids_variable_key = 'IDS-variable'

    def __getitem__(self, key: str) -> IDSVariableModel:
        return self.data[self.normalize(key)]

    def error_upper(self, key: str) -> IDSVariableModel:
        """Return error variable for given key.

        i.e. `t_i_ave` -> `t_i_ave_error_upper`
        """
        var = self[key.removesuffix(ERROR_SUFFIX)].copy()
        var.name += ERROR_SUFFIX
        var.path += ERROR_SUFFIX
        return var

    def normalize(self, *keys: str) -> str | tuple[str, ...]:
        """Normalize variable names (remove `$`)."""
        keys = tuple(key.lstrip(self._prefix) for key in keys)
        if len(keys) == 1:
            return keys[0]
        return keys

    def filter_type(self, type: str, *, invert: bool = False) -> VarLookup:
        """Filter all entries of given type."""
        cmp = operator.ne if invert else operator.eq
        return VarLookup({k: v for k, v in self.items() if cmp(v.type, type)})

    def groupby_type(self) -> dict[Hashable, list[IDSVariableModel]]:
        """Group entries by type."""
        grouped_ids_vars = groupby(self.values(), keyfunc=lambda var: var.type)
        return grouped_ids_vars

    def filter_ids(self, ids: str) -> VarLookup:
        """Filter all entries of given IDS."""
        ids_vars = self.filter_type(self._ids_variable_key)

        return VarLookup({k: v for k, v in ids_vars.items() if v.ids == ids})

    def groupby_ids(self) -> dict[Hashable, list[IDSVariableModel]]:
        """Group entries by IDS."""
        ids_vars = self.filter_type(self._ids_variable_key).values()

        grouped_ids_vars = groupby(ids_vars, keyfunc=lambda var: var.ids)
        return grouped_ids_vars

    def lookup(
        self, variables: Sequence[(str | IDSVariableModel)]
    ) -> list[IDSVariableModel]:
        """Helper function to look up a bunch of variables.

        If str, look up the variable from the `var_lookup`. Else, check if
        the variable is an `IDSVariableModel`.
        """
        var_models = []
        for var in variables:
            if isinstance(var, str):
                if var.endswith(ERROR_SUFFIX):
                    var = self.error_upper(var)
                else:
                    var = self[var]
            if not isinstance(var, IDSVariableModel):
                raise ValueError(
                    f'Cannot lookup variable with type {type(var)}')
            var_models.append(var)
        return var_models


class VariableConfigLoader:
    MODEL = VariableConfigModel
    VAR_DIR = 'imas2xarray'
    VAR_ENV = 'IMAS2XARRAY_VARDEF'
    MODULE = files('duqtools.imas2xarray.data')

    def __init__(self):
        self.paths = self.get_config_path()

    def load(self) -> VarLookup:
        """Load the variables config."""
        var_lookup = VarLookup()

        for path in self.paths:
            logger.debug(f'Loading variables from: {path}')
            with open(path) as f:
                var_config = parse_yaml_raw_as(self.MODEL, f)
            var_lookup.update(var_config.to_variable_dict())

        return var_lookup

    def get_config_path(self) -> tuple[Path, ...]:
        """Try to get the config file with variable definitions.

        Search order:
        1. environment variable
        (2. local directory, not sure if this should be implemented)
        3. config home (first $XDG_CONFIG_HOME/duqtools then `$HOME/.config/duqtools`)
        4. fall back to variable definitions in package
        """
        for paths in (
                self._get_paths_from_environment_variable(),
                self._get_paths_from_config_home(),
                self._get_paths_local_directory(),
        ):
            if paths:
                return paths

        return self._get_paths_fallback()

    def _get_paths_from_environment_variable(self) -> tuple[Path, ...] | None:
        env = os.environ.get(self.VAR_ENV)
        if env:
            path = Path(env)
            drc = path.parent

            if not drc.exists():
                raise OSError(
                    f'{path} defined by ${self.VAR_ENV} does not exist!')

            return tuple(drc.glob(path.name))

        return None

    def _get_paths_local_directory(self) -> tuple[Path, ...] | None:
        return None  # Not implemented

    def _get_paths_from_config_home(self) -> tuple[Path, ...] | None:
        config_home = os.environ.get('XDG_CONFIG_HOME', USER_CONFIG_HOME)

        drc = Path(config_home) / self.VAR_DIR
        if drc.exists():
            return tuple(drc.glob(VAR_FILENAME_GLOB))

        return None

    def _get_paths_fallback(self) -> tuple[Path, ...]:
        assert self.MODULE.is_dir()

        if isinstance(self.MODULE, PosixPath):
            drc = self.MODULE
        else:
            drc = self.MODULE._paths[0]  # type: ignore

        return tuple(drc.glob(VAR_FILENAME_GLOB))


var_lookup = VariableConfigLoader().load()
