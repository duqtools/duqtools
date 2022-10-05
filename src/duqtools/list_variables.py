from pydantic import ValidationError

from duqtools.config import cfg, var_lookup


def list_variables(*, config, **kwargs):
    """List variables in `variables.yaml` and config/`duqtools.yaml` if
    present.

    Parameters
    ----------
    config : str
        Name of the config file to use
    **kwargs
        Unused.
    """
    try:
        cfg.parse_file(config)
    except FileNotFoundError:
        print(f'Could not find: {config}')
    except ValidationError as e:
        exit(e)
        print(f'*: defined by {config}')
    finally:
        extra_variables = cfg.extra_variables.to_variable_dict(
        ) if cfg.extra_variables else {}

    print('variables.yaml')
    for name, var in var_lookup.items():
        star = '*' if name in extra_variables else ''
        print('    ', var.name, star)

    print()
