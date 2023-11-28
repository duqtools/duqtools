from __future__ import annotations

from ._config import CFG, Config, load_config
from ._variables import var_lookup

__all__ = [
    'CFG',
    'Config',
    'load_config',
    'var_lookup',
]
