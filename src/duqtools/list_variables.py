from itertools import filterfalse, tee
from typing import Dict, List

import click
from pydantic import ValidationError

from duqtools.config import cfg, var_lookup

from .utils import groupby

cs = click.style

ST_ITEMS = {'fg': 'green', 'bold': True}
ST_HEADER = {'fg': 'red', 'bold': True}
ST_INFO = {'fg': 'white', 'bold': False}


def partition(pred, iterable):
    """Use a predicate to partition entries into false entries and true
    entries.

    From: https://docs.python.org/3/library/itertools.html
    """
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)


def list_group(group: List, extra_variables: Dict):
    group = sorted(group, key=lambda var: var.name)

    for var in group:
        star = cs('*', **ST_HEADER) if var.name in extra_variables else ''

        name = cs(f'{var.name}', **ST_ITEMS)

        try:
            sub = cs(f'({var.path})', **ST_INFO)
        except AttributeError:
            sub = cs(f'({var.type})', **ST_INFO)

        print(f'    - {star}{name} {sub}')


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

    all_variables = var_lookup.values()

    other_variables, ids_variables = partition(
        lambda var: var.type == 'IDS-variable', all_variables)

    grouped_ids_vars = groupby(ids_variables, keyfunc=lambda var: var.ids)

    for root_ids, group in grouped_ids_vars.items():
        click.secho(f'\nIDS-variable - {root_ids}:', **ST_HEADER)
        list_group(group, extra_variables)

    grouped_other_vars = groupby(other_variables, keyfunc=lambda var: var.type)

    for var_type, group in grouped_other_vars.items():
        click.secho(f'\n{var_type}:', **ST_HEADER)
        list_group(group, extra_variables)
