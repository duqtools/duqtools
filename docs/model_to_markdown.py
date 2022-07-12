"""
Usage:

    python model_to_markdown.py <config object>

Where <config> object must be a top-level config object, i.e. status, submit
"""

import sys

from ruamel import yaml

from duqtools.config import cfg

schema = cfg.schema()

models = sys.argv[1:]

for model_str in models:
    model = getattr(cfg, model_str)

    schema = model.schema()

    print(f'### The `{model_str}` config')
    print()
    print(schema['description'])
    for name, prop in schema['properties'].items():
        print()
        print(f'`{name}`')
        print(f": {prop['description']} (default: `{prop['default']}`)")

    print()
    print('### Example')
    print()
    print('```yaml title="duqtools.yaml"')
    print(yaml.dump({'status': model.dict()}, default_flow_style=False))
    print('```')
    print()
