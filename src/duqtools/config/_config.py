"""Config class containing all configs, can be used with:

    from duqtools.config import cfg
    cfg.<variable you want>

To update the config:

    load_config('duqtools.yaml')
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from ..schema.cli import ConfigModel


class Config(ConfigModel):
    ...

    @staticmethod
    def _update_global_config(new_cfg: Config):
        from ._variables import var_lookup

        if new_cfg.extra_variables:
            var_lookup.update(new_cfg.extra_variables.to_variable_dict())

        cfg.__dict__.update(new_cfg.__dict__)

    @classmethod
    def from_dict(cls, mapping: dict):
        new_cfg = cls.parse_obj(mapping)
        cls._update_global_config(new_cfg)
        return new_cfg

    @classmethod
    def from_file(cls, path: Union[str, Path]):
        new_cfg = cls.parse_file(path)

        cls._update_global_config(new_cfg)

        for obj in (cfg, new_cfg):
            obj._path = path

        return new_cfg


def load_config(path: Union[str, Path]) -> Config:
    return Config.from_file(path)


cfg = Config.construct()
