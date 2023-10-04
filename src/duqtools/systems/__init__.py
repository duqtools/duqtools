"""This module contains adapters to interface with various simulation
suites."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base_system import AbstractSystem
    from .config import Config


def get_system(cfg: Config) -> AbstractSystem:
    """Get the system to do operations with."""
    System: Any = None

    if (cfg.system.name in ('jetto', 'jetto-v220922', 'jetto-v230123')):
        from .jetto import JettoSystemV220922
        System = JettoSystemV220922

    elif (cfg.system.name == 'jetto-v210921'):
        from .jetto import JettoSystemV210921
        System = JettoSystemV210921

    elif (cfg.system.name == 'ets6'):
        from .ets import Ets6System
        System = Ets6System

    elif (cfg.system.name in (None, 'nosystem')):
        from .no_system import NoSystem
        System = NoSystem

    else:
        raise NotImplementedError(
            f'system {cfg.system.name} is not implemented')

    return System(cfg=cfg)
