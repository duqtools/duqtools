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


cfg = Config.construct()
