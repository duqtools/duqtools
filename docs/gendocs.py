"""This script read the jinja2 templates from the ./templates directory, and
auto-fills the place-hodlers with the pydantic models defined in this file.

To generate the docs:

python gendocs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import mkdocs_gen_files

from duqtools.config._schema_create import CreateConfigModel
from duqtools.config._schema_root import ConfigModel
from duqtools.ids._schema import ImasBaseModel
from duqtools.schema import (
    ARange,
    IDSOperationDim,
    IDSVariableModel,
    LinSpace,
    OperationDim,
)
from duqtools.schema.data_location import DataLocation
from duqtools.systems.jetto import JettoVar, JettoVariableModel, JsetField, NamelistField
from duqtools.systems.models import StatusConfigModel, SubmitConfigModel

this_dir = Path(__file__).parent
sys.path.append(str(this_dir))

from templates import get_template  # noqa

SUBDIR = 'config'

objects = {
    ARange,
    ConfigModel,
    CreateConfigModel,
    DataLocation,
    IDSOperationDim,
    IDSVariableModel,
    ImasBaseModel,
    JettoVariableModel,
    JettoVar,
    JsetField,
    NamelistField,
    LinSpace,
    OperationDim,
    StatusConfigModel,
    SubmitConfigModel,
}
schemas = {
    f'schema_{obj.__name__}': obj.model_json_schema()  # type: ignore
    for obj in objects
}
for page in 'index', 'status', 'submit', 'create':
    template = get_template(f'template_{page}.md')

    rendered = template.render(**schemas)

    filename = f'{SUBDIR}/{page}.md'

    with mkdocs_gen_files.open(filename, 'w') as file:
        print(f'Writing {file.name}')
        file.write(rendered)
