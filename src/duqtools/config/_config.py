"""Config class containing all configs, can be used with:

```
from duqtools.config import CFG
CFG.<variable you want>
```

To update the config:

```
load_config('duqtools.yaml')
```
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from pydantic_yaml import parse_yaml_raw_as

from ._schema_root import ConfigModel


class Config(ConfigModel):

    @staticmethod
    def _update_global_config(cfg: Config):
        from ._variables import var_lookup

        if cfg.extra_variables:
            var_lookup.update(cfg.extra_variables.to_variable_dict())

        CFG.__dict__.update(cfg.__dict__)

    @classmethod
    def from_dict(cls, mapping: dict) -> Config:
        """Parse config from dictionary and update global config (CFG).

        Parameters
        ----------
        path : Union[str, Path]
            Path to config.

        Returns
        -------
        cfg : Config
            Return instance of Config class.
        """
        cfg = cls.model_validate(mapping)
        cls._update_global_config(cfg)
        return cfg

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> Config:
        """Read config from file and update global config (CFG).

        Parameters
        ----------
        path : Union[str, Path]
            Path to config.

        Returns
        -------
        cfg : Config
            Return instance of Config class.
        """
        with open(path) as f:
            cfg = parse_yaml_raw_as(cls, f)

        cls._update_global_config(cfg)

        for obj in (CFG, cfg):
            obj._path = path

        return cfg


def load_config(path: Union[str, Path]) -> Config:
    return Config.from_file(path)


CFG = Config.model_construct()
