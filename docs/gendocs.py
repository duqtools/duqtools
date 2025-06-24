"""This script read the jinja2 templates from the ./templates directory, and
auto-fills the place-hodlers with the pydantic models defined in this file.

To generate the docs:

python gendocs.py
"""
from __future__ import annotations

from pathlib import Path

import mkdocs_gen_files
from imas2xarray import Variable
from jinja2 import Environment, FileSystemLoader
from pydantic_yaml import to_yaml_str

from duqtools.config import var_lookup
from duqtools.config._schema_create import CreateConfigModel
from duqtools.config._schema_root import ConfigModel
from duqtools.ids._schema import ImasBaseModel
from duqtools.schema import (
    ARange,
    IDSOperationDim,
    LinSpace,
    OperationDim,
)
from duqtools.systems.jetto import JettoVar, JettoVariableModel
from duqtools.systems.models import StatusConfigModel, SubmitConfigModel

THIS_DIR = Path(__file__).parent


def get_template(path):
    drc = path.parent
    page = path.name

    file_loader = FileSystemLoader(THIS_DIR / drc)
    environment = Environment(loader=file_loader, autoescape=False)
    environment.filters['to_yaml_str'] = to_yaml_str

    return environment.get_template(page)


def gen_docs():
    objects = {
        ARange,
        ConfigModel,
        CreateConfigModel,
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
            #'usage.template.md',
            'systems/status.template.md',
            'systems/submit.template.md',
    ):
        path = Path(page)

        template = get_template(path)

        rendered = template.render(**schemas)

        stem, *_ = path.name.partition('.')
        new_path = path.with_name(stem).with_suffix('.md')

        with mkdocs_gen_files.open(new_path, 'w') as file:
            print(f'Writing {file.name}')
            file.write(rendered)


def gen_jetto_variables():
    objects = {
        JettoVariableModel,
        JettoVar,
    }
    schemas = {
        f'schema_{obj.__name__}': obj.model_json_schema()  # type: ignore
        for obj in objects
    }

    path = Path('systems/variables.template.md')

    template = get_template(path)

    variable_groups = var_lookup.groupby_type()
    variable_groups.pop('IDS-variable')

    def sort_var_groups_in_dict(dct):
        for name in dct:
            dct[name] = sorted(dct[name], key=lambda var: var.name)

    sort_var_groups_in_dict(variable_groups)

    rendered = template.render(variable_groups=variable_groups, **schemas)

    stem, *_ = path.name.partition('.')
    new_path = path.with_name(stem).with_suffix('.md')

    with mkdocs_gen_files.open(new_path, 'w') as file:
        print(f'Writing {file.name}')
        file.write(rendered)


gen_docs()
gen_jetto_variables()
