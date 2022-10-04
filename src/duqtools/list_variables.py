from pydantic import ValidationError

from duqtools.config import cfg, var_lookup


def list_variables(config, **kwargs):
    print('variables.yaml')
    for name, var in var_lookup.items():
        print('    ', var.name, var.type)

    print()

    try:
        cfg.parse_file(config)
    except FileNotFoundError:
        print(f'Could not find: {config}')
    except ValidationError as e:
        exit(e)
    else:
        print(config)
        for var in config.extra_variables:
            print('    ', var)
