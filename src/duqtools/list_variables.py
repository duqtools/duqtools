from collections import defaultdict
from typing import Any, Callable, Dict, Hashable, Iterable, List

import click
from pydantic import ValidationError

from duqtools.config import cfg, var_lookup


def groupby(iterable: Iterable,
            keyfunc: Callable) -> Dict[Hashable, List[Any]]:
    """Group iterable by key function.
    The items are grouped by the value that is returned by the `keyfunc`
    Parameters
    ----------
    iterable : list, tuple or iterable
        List of items to group
    keyfunc : callable
        Used to determine the group of each item. These become the keys
        of the returned dictionary

    Returns
    -------
    grouped : dict
        Returns a dictionary with the grouped values.
    """
    grouped = defaultdict(list)
    for item in iterable:
        key = keyfunc(item)
        grouped[key].append(item)

    return grouped


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
    cs = click.style
    st_items = {'fg': 'green', 'bold': True}
    st_header = {'fg': 'red', 'bold': True}
    st_info = {'fg': 'white', 'bold': False}

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

    grouped = groupby(var_lookup.values(), keyfunc=lambda var: var.type)

    for var_type, group in grouped.items():
        click.secho(f'\n{var_type}:', **st_header)

        for var in group:
            star = cs('*', **st_header) if var.name in extra_variables else ''

            name = cs(f'{var.name}', **st_items)

            try:
                sub = cs(f'({var.ids}/{var.path})', **st_info)
            except AttributeError:
                sub = cs(f'({var.type})', **st_info)

            print(f'    - {star}{name} {sub}')
