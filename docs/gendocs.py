from ruamel import yaml
from templates import get_template

from duqtools.config import cfg

models = {'status': cfg.status, 'submit': cfg.submit, 'plot': cfg.plot}

for name, model in models.items():
    template = get_template(f'template_{name}.md')

    yaml_example = yaml.dump(
        {
            name: yaml.safe_load(model.json(exclude_none=True))  # type: ignore
        },
        default_flow_style=False).strip()

    if name == 'plot':
        plot_schema = model.plots[0].schema()  # type: ignore

        rendered = template.render(
            model=model,
            schema=model.schema(),
            plot_schema=plot_schema,
            yaml_example=yaml_example,
        )

    else:
        rendered = template.render(
            model=model,
            schema=model.schema(),
            yaml_example=yaml_example,
        )

    filename = f'{name}.md'

    with open(filename, 'w') as file:
        file.write(rendered)
