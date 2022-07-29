"""This script read the jinja2 templates from the ./templates directory, and
auto-fills the place-hodlers with the pydantic models defined in this file.

To generate the docs:

    python gendocs.py
"""

import sys
from pathlib import Path

import mkdocs_gen_files
from ruamel import yaml

from duqtools.config import cfg

this_dir = Path(__file__).parent

sys.path.append(str(this_dir))

from templates import get_template  # noqa

SUBDIR = 'config'

models = {
    'introduction': cfg,
    'status': cfg.status,
    'submit': cfg.submit,
    'create': cfg.create,
    'merge': cfg.merge,
}


def model2config(key: str, model) -> str:
    """Generate example config for model."""
    data = yaml.safe_load(model.json(exclude_none=True))  # type: ignore

    if key != 'introduction':
        data = {
            key: data,
        }

    return yaml.dump(data, default_flow_style=False).strip()


extra_schemas = {}
extra_yamls = {}

if 'create' in models:
    from duqtools.schema import (ARange, IDSOperationDim, ImasBaseModel,
                                 LinSpace)

    extra_schemas['ops_schema'] = IDSOperationDim.schema()
    extra_schemas['data_loc_schema'] = cfg.create.data.schema()

    extra_schemas['linspace_schema'] = LinSpace.schema()
    extra_schemas['arange_schema'] = ARange.schema()

    extra_schemas['imas_basemodel_schema'] = ImasBaseModel.schema()

    extra_yamls['data_loc_yaml'] = model2config('data', cfg.create.data)

if 'introduction' in models:
    extra_schemas['wd_schema'] = cfg.workspace.schema()
    extra_yamls['wd_yaml'] = model2config('workspace', cfg.workspace)

    from duqtools.jetto import JettoSystem
    from duqtools.system import DummySystem

    extra_schemas['jetto_schema'] = JettoSystem.schema()
    extra_schemas['dummy_schema'] = DummySystem.schema()

if 'merge' in models:
    extra_schemas['wd_schema'] = cfg.workspace.schema()
    extra_yamls['wd_yaml'] = model2config('workspace', cfg.workspace)

    from duqtools.jetto import JettoSystem
    from duqtools.system import DummySystem

    extra_schemas['jetto_schema'] = JettoSystem.schema()
    extra_schemas['dummy_schema'] = DummySystem.schema()

for name, model in models.items():
    template = get_template(f'template_{name}.md')

    yaml_example = model2config(name, model)

    rendered = template.render(
        schema=model.schema(),
        yaml_example=yaml_example,
        **extra_schemas,
        **extra_yamls,
    )

    filename = f'{SUBDIR}/{name}.md'

    with mkdocs_gen_files.open(filename, 'w') as file:
        print(f'Writing {file.name}')
        file.write(rendered)
