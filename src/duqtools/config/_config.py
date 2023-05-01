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


def load_config(path: Union[str, Path]) -> Config:
    global cfg

    new_cfg = Config.parse_file(path)

    from ._variables import var_lookup

    if new_cfg.extra_variables:
        var_lookup.update(new_cfg.extra_variables.to_variable_dict())

    new_cfg._path = path

    cfg.__dict__.update(new_cfg.__dict__)

    return new_cfg


cfg = Config.construct()
