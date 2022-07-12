"""
Usage:

    python model_to_markdown.py <config object>

Where <config> object must be a top-level config object, i.e. status, submit
"""

from ruamel import yaml

from duqtools.config import cfg

schema = cfg.schema()

models = ['create']

definitions = [
    'IDSOperationSet',
    'IDSSamplerSet',
]

for model_str in models:
    model = getattr(cfg, model_str)

    schema = model.schema()

    print(f'## The `{model_str}` config')
    print()
    print(schema['description'])
    for name, prop in schema['properties'].items():
        print()
        print(f'`{name}`')
        print(f": {prop['description']}")

    print()
    print('### Example')
    print()
    print('```yaml title="duqtools.yaml"')
    print(yaml.dump({model_str: model.dict()}, default_flow_style=False))
    print('```')
    print()

print('### Definitions')
print()

for defn_str in definitions:

    defn = schema['definitions'][defn_str]

    print(f'#### `{defn["title"]}`')
    print()
    print(f"{defn['description']}")

    for name, prop in defn['properties'].items():
        desc = prop['description']
        print()
        print(f'`{name}`')
        print(f': {desc}')

    print()
