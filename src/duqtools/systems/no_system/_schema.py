from __future__ import annotations

from typing import Literal

from pydantic import Field

from ..models import SystemModel


class NoSystemModel(SystemModel):
    name: Literal[None, 'nosystem'] = Field(None, description='No system.')
