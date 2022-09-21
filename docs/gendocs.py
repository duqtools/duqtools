"""This script read the jinja2 templates from the ./templates directory, and
auto-fills the place-hodlers with the pydantic models defined in this file.

To generate the docs:

    python gendocs.py
"""

import sys
from pathlib import Path

import mkdocs_gen_files

from duqtools.config import cfg
from duqtools.schema import OperationDim

this_dir = Path(__file__).parent

sys.path.append(str(this_dir))

from templates import get_template  # noqa

SUBDIR = 'config'

pages = 'introduction', 'status', 'submit', 'create', 'merge'

schemas = {
    'schema': cfg.schema(),
    'status_schema': cfg.status.schema(),
    'submit_schema': cfg.submit.schema(),
    'create_schema': cfg.create.schema(),
    'merge_schema': cfg.merge.schema(),
}

# Repair auto replace of init:
cfg.create.dimensions = [
    OperationDim(variable='t_i_average'),
    OperationDim(variable='zeff'),
    OperationDim(variable='major_radius', values=[296, 297], operator='copyto')
]

if 'create' in pages:
    from duqtools.schema import (ARange, IDSOperationDim, ImasBaseModel,
                                 LinSpace)

    schemas['ops_schema'] = IDSOperationDim.schema()
    schemas['data_loc_schema'] = cfg.create.data.schema()

    schemas['linspace_schema'] = LinSpace.schema()
    schemas['arange_schema'] = ARange.schema()

    schemas['imas_basemodel_schema'] = ImasBaseModel.schema()

if 'introduction' in pages:
    from duqtools.jettoduqtools import JettoDuqtoolsSystem
    from duqtools.jettopythontools import JettoPythonToolsSystem
    from duqtools.system import DummySystem

    schemas['wd_schema'] = cfg.workspace.schema()

    schemas['jetto_schema'] = JettoDuqtoolsSystem.schema()
    schemas['jetto_pythontools_schema'] = JettoPythonToolsSystem.schema()
    schemas['dummy_schema'] = DummySystem.schema()

    schemas['ids_variable_schema'] = cfg.variables.__root__[0].schema()
    schemas['jetto_variable_schema'] = cfg.variables.__root__[4].schema()

if 'merge' in pages:
    schemas['wd_schema'] = cfg.workspace.schema()
    schemas['merge_op_schema'] = cfg.merge.plan[0].schema()

for page in pages:
    template = get_template(f'template_{page}.md')

    rendered = template.render(**schemas, )

    filename = f'{SUBDIR}/{page}.md'

    with mkdocs_gen_files.open(filename, 'w') as file:
        print(f'Writing {file.name}')
        file.write(rendered)
