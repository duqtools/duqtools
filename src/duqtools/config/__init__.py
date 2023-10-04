from __future__ import annotations

from ._config import CFG, Config, load_config
from ._variables import lookup_vars, var_lookup

__all__ = [
    'CFG',
    'Config',
    'load_config',
    'lookup_vars',
    'var_lookup',
]
