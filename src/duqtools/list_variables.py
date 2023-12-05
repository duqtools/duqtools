from __future__ import annotations

import typing
from typing import TYPE_CHECKING

import click

from duqtools.config import var_lookup

if TYPE_CHECKING:
    from duqtools.config import Config

cs = click.style

ST_ITEMS = {'fg': 'green', 'bold': True}
ST_HEADER = {'fg': 'red', 'bold': True}
ST_INFO = {'fg': 'white', 'bold': False}


@typing.no_type_check
def list_group(group: list, extra_variables: dict):
    group = sorted(group, key=lambda var: var.name)

    for var in group:
        star = cs('*', **ST_HEADER) if var.name in extra_variables else ''

        name = cs(f'{var.name}', **ST_ITEMS)

        try:
            sub = cs(f'({var.path})', **ST_INFO)
        except AttributeError:
            sub = cs(f'({var.type})', **ST_INFO)

        click.echo(f'    - {star}{name} {sub}')


@typing.no_type_check
def list_variables(*, cfg: Config, **kwargs):
    """List variables in `variables.yaml` and config/`duqtools.yaml` if
    present.

    Parameters
    ----------
    config : Config
        Duqtools config.
    **kwargs
        Unused.
    """
    extra_variables = cfg.extra_variables.to_variable_dict(
    ) if cfg.extra_variables else {}

    grouped_ids_vars = var_lookup.groupby_ids()

    for root_ids, group in grouped_ids_vars.items():
        click.secho(f'\nIDS-variable - {root_ids}:', **ST_HEADER)
        list_group(group, extra_variables)

    grouped_other_vars = var_lookup.groupby_type()
    grouped_other_vars.pop('IDS-variable', None)

    for var_type, group in grouped_other_vars.items():
        click.secho(f'\n{var_type}:', **ST_HEADER)
        list_group(group, extra_variables)
