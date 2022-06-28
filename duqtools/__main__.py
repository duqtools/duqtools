import logging
from functools import wraps

import click
import coverage

from duqtools.config import cfg

logger = logging.getLogger(__name__)
coverage.process_startup()


def global_params(func):

    @click.option('-c',
                  '--config',
                  default='duqtools.yaml',
                  help='Path to config.')
    @click.option('--debug',
                  is_flag=True,
                  help='Enable debug print statements.')
    @click.option('--force',
                  is_flag=True,
                  help='Force the action you want to take.')
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@click.group()
@global_params
@click.pass_context
def cli(ctx, config='duqtools.yaml', debug=False, **kwargs):
    """This is the docstring for duqtools."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.debug('Params: %s', ctx.params)
    logger.debug('Subcommand: %s', ctx.invoked_subcommand)

    if ctx.invoked_subcommand != 'init':
        cfg.read(config)


@cli.command('init')
@click.option('--full',
              is_flag=True,
              help='Create a config file with all possible config values.')
@global_params
def cli_init(**kwargs):
    """Create a default config file."""
    from .init import init
    init(**kwargs)


@cli.command('create')
@global_params
def cli_create(**kwargs):
    """Create the UQ run files."""
    from .create import create
    create(**kwargs)


@cli.command('submit')
@global_params
def cli_submit(**kwargs):
    """Submit the UQ runs."""
    from .submit import submit
    submit(**kwargs)


@cli.command('status')
@click.option('--detailed', is_flag=True, help='Detailed info on progress')
@click.option('--progress', is_flag=True, help='Fancy progress bar')
@global_params
def cli_status(**kwargs):
    """Print the status of the UQ runs."""
    from .status import status
    status(**kwargs)


@cli.command('plot')
@global_params
def cli_plot(**kwargs):
    """Analyze the results and generate a report'."""
    from .plot import plot
    plot(**kwargs)


@cli.command('clean')
@click.option('--out', is_flag=True, help='Remove output data.')
@global_params
def cli_clean(**kwargs):
    """Delete generated IDS data and the run dir."""
    from .cleanup import cleanup
    cleanup(**kwargs)


@cli.command('dash')
@global_params
def cli_dash(**kwargs):
    """Open dashboard for evaluating IDS data."""
    from .dash import dash
    dash(**kwargs)


if __name__ == '__main__':
    cli()
