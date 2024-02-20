"""This script read the jinja2 templates from the ./templates directory, and
auto-fills the place-hodlers with the pydantic models defined in this file.

To generate the docs:

python gendocs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import mkdocs_gen_files
from imas2xarray import Variable

from duqtools.config._schema_create import CreateConfigModel
from duqtools.config._schema_root import ConfigModel
from duqtools.ids._schema import ImasBaseModel
from duqtools.schema import (
    ARange,
    IDSOperationDim,
    LinSpace,
    OperationDim,
)
from duqtools.schema.data_location import DataLocation
from duqtools.systems.jetto import JettoVar, JettoVariableModel
from duqtools.systems.models import StatusConfigModel, SubmitConfigModel

this_dir = Path(__file__).parent
sys.path.append(str(this_dir))

from templates import get_template  # noqa

objects = {
    ARange,
    ConfigModel,
    CreateConfigModel,
    DataLocation,
    IDSOperationDim,
    ImasBaseModel,
    JettoVariableModel,
    JettoVar,
    LinSpace,
    OperationDim,
    StatusConfigModel,
    SubmitConfigModel,
    Variable,
}
schemas = {
    f'schema_{obj.__name__}': obj.model_json_schema()  # type: ignore
    for obj in objects
}
for page in (
        'usage',
        'systems_status',
        'systems_submit',
):
    template = get_template(f'template_{page}.md')

    rendered = template.render(**schemas)

    filename = '/'.join(page.split('_')) + '.md'

    with mkdocs_gen_files.open(filename, 'w') as file:
        print(f'Writing {file.name}')
        file.write(rendered)
