from __future__ import annotations

import sys
from pathlib import Path

import mkdocs_gen_files

from duqtools.config import var_lookup

this_dir = Path(__file__).parent

sys.path.append(str(this_dir))

from templates import get_template  # noqa

template = get_template('template_variables.md')

grouped_ids_vars = var_lookup.groupby_ids()

grouped_other_vars = var_lookup.groupby_type()
grouped_other_vars.pop('IDS-variable')


def sort_var_groups_in_dict(dct):
    for name in dct:
        dct[name] = sorted(dct[name], key=lambda var: var.name)


sort_var_groups_in_dict(grouped_ids_vars)
sort_var_groups_in_dict(grouped_other_vars)

rendered = template.render(ids_vars=grouped_ids_vars,
                           other_vars=grouped_other_vars)

filename = 'variables.md'

with mkdocs_gen_files.open(filename, 'w') as file:
    print(f'Writing {file.name}')
    file.write(rendered)
