import sys
from pathlib import Path

import mkdocs_gen_files

from duqtools.config import var_lookup
from duqtools.utils import groupby, partition

this_dir = Path(__file__).parent

sys.path.append(str(this_dir))

from templates import get_template  # noqa

template = get_template('template_variables.md')

all_variables = var_lookup.values()

other_variables, ids_variables = partition(
    lambda var: var.type == 'IDS-variable', all_variables)

grouped_ids_vars = groupby(ids_variables, keyfunc=lambda var: var.ids)
grouped_other_vars = groupby(other_variables, keyfunc=lambda var: var.type)


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
