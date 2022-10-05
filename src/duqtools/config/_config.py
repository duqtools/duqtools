from __future__ import annotations

from ..schema.cli import ConfigModel


class Config(ConfigModel):
    """Config class containing all configs, can be used with:

        from duqtools.config import cfg
        cfg.<variable you want>

    To update the config:

        cfg.parse_file('duqtools.yaml')
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Config._instance:
            Config._instance = object.__new__(cls)
        return Config._instance

    def parse_file(self, *args, **kwargs):
        """Add extra variables to variable lookup table."""
        super().parse_file(*args, **kwargs)
        from ._variables import var_lookup
        if self.extra_variables:
            var_lookup.update(self.extra_variables.to_variable_dict())


cfg = Config.construct()
