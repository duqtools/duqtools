import sys
from pathlib import Path

import mkdocs_gen_files

from duqtools.config import var_lookup
from duqtools.utils import groupby

this_dir = Path(__file__).parent

sys.path.append(str(this_dir))

from templates import get_template  # noqa

template = get_template('template_variables.md')

var_groups = groupby(var_lookup.values(), keyfunc=lambda var: var.type)

rendered = template.render(var_groups=var_groups)

filename = 'variables.md'

with mkdocs_gen_files.open(filename, 'w') as file:
    print(f'Writing {file.name}')
    file.write(rendered)
