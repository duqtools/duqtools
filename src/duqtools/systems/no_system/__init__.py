"""This module contains a 'no system' System.

It is meant as a template for adding new Systems or
running `duqtools` without system, e.g. for inclusion in data
manipulation workflows.
"""
from __future__ import annotations

from ._schema import NoSystemModel
from ._system import NoSystem

__all__ = [
    'NoSystem',
    'NoSystemModel',
]
