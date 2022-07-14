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
    'plot': cfg.plot,
    'create': cfg.create,
}


def model2config(key: str, model) -> str:
    """Generate example config for model."""
    return yaml.dump(
        {
            key: yaml.safe_load(model.json(exclude_none=True))  # type: ignore
        },
        default_flow_style=False).strip()


extra_schemas = {}
extra_yamls = {}

if 'plot' in models:
    from duqtools.config._plot import Plot

    extra_schemas['plot_schema'] = Plot.schema()

if 'create' in models:
    from duqtools.ids.operation import IDSOperationSet
    from duqtools.ids.sampler import IDSSamplerSet

    extra_schemas['ops_schema'] = IDSOperationSet.schema()
    extra_schemas['sampler_schema'] = IDSSamplerSet.schema()
    extra_schemas['data_loc_schema'] = cfg.create.data.schema()

    extra_yamls['data_loc_yaml'] = model2config('data', cfg.create.data)

if 'introduction' in models:
    extra_schemas['wd_schema'] = cfg.workspace.schema()
    extra_yamls['wd_yaml'] = model2config('workspace', cfg.workspace)

    from duqtools.config.system import DummySystem
    from duqtools.jetto.system import JettoSystem

    extra_schemas['system_schema'] = cfg.system.schema()
    extra_schemas['jetto_schema'] = DummySystem.schema()
    extra_schemas['dummy_schema'] = JettoSystem.schema()
    extra_yamls['system_yaml'] = model2config('system', cfg.system)

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
