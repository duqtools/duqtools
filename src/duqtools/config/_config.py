from __future__ import annotations

from ..schema.cli import ConfigModel


class Config(ConfigModel):
    """Config class containing all configs, is a singleton and can be used with
    import duqtools.config.Config as Cfg Cfg().<variable you want>"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        # Make it a singleton
        if not Config._instance:
            Config._instance = object.__new__(cls)
        return Config._instance


cfg = Config()
