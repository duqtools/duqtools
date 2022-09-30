"""This script read the jinja2 templates from the ./templates directory, and
auto-fills the place-hodlers with the pydantic models defined in this file.

To generate the docs:

    python gendocs.py
"""
import sys
from pathlib import Path

import mkdocs_gen_files

from duqtools.jettoduqtools import JettoDuqtoolsSystem
from duqtools.jettopythontools import JettoPythonToolsSystem
from duqtools.schema import (ARange, IDSOperationDim, IDSVariableModel,
                             ImasBaseModel, JettoVariableModel, LinSpace,
                             OperationDim)
from duqtools.schema.cli import (ConfigModel, CreateConfigModel,
                                 MergeConfigModel, MergeStep,
                                 StatusConfigModel, SubmitConfigModel)
from duqtools.schema.data_location import DataLocation
from duqtools.schema.workdir import WorkDirectoryModel
from duqtools.system import DummySystem

this_dir = Path(__file__).parent
sys.path.append(str(this_dir))

from templates import get_template  # noqa

SUBDIR = 'config'

objects = {
    ARange,
    ConfigModel,
    CreateConfigModel,
    DataLocation,
    DummySystem,
    IDSOperationDim,
    IDSVariableModel,
    ImasBaseModel,
    JettoDuqtoolsSystem,
    JettoPythonToolsSystem,
    JettoVariableModel,
    LinSpace,
    MergeConfigModel,
    MergeStep,
    OperationDim,
    StatusConfigModel,
    SubmitConfigModel,
    WorkDirectoryModel,
}

schemas = {
    f'schema_{obj.__name__}': obj.schema()  # type: ignore
    for obj in objects
}

for page in 'introduction', 'status', 'submit', 'create', 'merge':
    template = get_template(f'template_{page}.md')

    rendered = template.render(**schemas)

    filename = f'{SUBDIR}/{page}.md'

    with mkdocs_gen_files.open(filename, 'w') as file:
        print(f'Writing {file.name}')
        file.write(rendered)
