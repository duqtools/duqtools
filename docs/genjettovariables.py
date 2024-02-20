from __future__ import annotations

import sys
from pathlib import Path

import mkdocs_gen_files

from duqtools.config import var_lookup
from duqtools.systems.jetto import JettoVar, JettoVariableModel

this_dir = Path(__file__).parent
sys.path.append(str(this_dir))

from templates import get_template  # noqa

objects = {
    JettoVariableModel,
    JettoVar,
}
schemas = {
    f'schema_{obj.__name__}': obj.model_json_schema()  # type: ignore
    for obj in objects
}

this_dir = Path(__file__).parent

sys.path.append(str(this_dir))

from templates import get_template  # noqa

template = get_template('template_systems_variables.md')

variable_groups = var_lookup.groupby_type()
variable_groups.pop('IDS-variable')


def sort_var_groups_in_dict(dct):
    for name in dct:
        dct[name] = sorted(dct[name], key=lambda var: var.name)


sort_var_groups_in_dict(variable_groups)

rendered = template.render(variable_groups=variable_groups, **schemas)

filename = 'jetto/jetto_variables.md'

with mkdocs_gen_files.open(filename, 'w') as file:
    print(f'Writing {file.name}')
    file.write(rendered)
