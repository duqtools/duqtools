from ruamel import yaml
from templates import get_template

from duqtools.config import cfg

models = {
    'status': cfg.status, 
    'submit': cfg.submit, 
    'plot': cfg.plot, 
    'create': cfg.create,
}

extra_schemas = {}

# plot

from duqtools.config.plot import Plot

extra_schemas['plot_schema'] = Plot.schema()

# create

from duqtools.ids.operation import IDSOperationSet
from duqtools.ids.sampler import IDSSamplerSet

extra_schemas['ops_schema'] = IDSOperationSet.schema()
extra_schemas['sampler_schema'] = IDSSamplerSet.schema()


for name, model in models.items():
    template = get_template(f'template_{name}.md')

    yaml_example = yaml.dump(
        {
            name: yaml.safe_load(model.json(exclude_none=True))  # type: ignore
        },
        default_flow_style=False).strip()

    kwargs = extra_schemas[name]

    rendered = template.render(
        schema=model.schema(),
        yaml_example=yaml_example,
        **kwargs,
    )

    filename = f'{name}.md'

    with open(filename, 'w') as file:
        file.write(rendered)
