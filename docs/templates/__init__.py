"""Collection of jinja2 templates to render md output."""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic_yaml import to_yaml_str

TEMPLATE_DIR = Path(__file__).parent
file_loader = FileSystemLoader(str(TEMPLATE_DIR))
environment = Environment(loader=file_loader, autoescape=False)
environment.filters['to_yaml_str'] = to_yaml_str

get_template = environment.get_template

__all__ = [
    'get_template',
]
