import logging
from getpass import getuser

import click
import coverage

from duqtools.config import cfg

logger = logging.getLogger(__name__)
coverage.process_startup()


def config_option(f):

    def callback(ctx, param, config):
        logger.debug('Subcommand: %s', ctx.invoked_subcommand)
        if ctx.command.name != 'init':
            cfg.parse_file(config)

        return config

    return click.option('-c',
                        '--config',
                        default='duqtools.yaml',
                        help='Path to config.',
                        callback=callback)(f)


def debug_option(f):

    def callback(ctx, param, debug):
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)

        return debug

    return click.option('--debug',
                        is_flag=True,
                        help='Enable debug print statements.',
                        callback=callback)(f)


def dry_run_option(f):

    def callback(ctx, param, dry_run):
        if dry_run:
            logger.info('--dry-run enabled')
            cfg.dry_run = True

        return dry_run

    return click.option('--dry-run',
                        is_flag=True,
                        help='Execute without any side-effects.',
                        callback=callback)(f)


def common_options(func):
    for wrapper in (debug_option, config_option, dry_run_option):
        # config_option MUST BE BEFORE dry_run_option
        func = wrapper(func)
    return func


@click.group()
def cli(**kwargs):
    """For more information, check out the documentation:

    https://duqtools.readthedocs.io
    """
    pass


@cli.command('init')
@common_options
@click.option('--full',
              is_flag=True,
              help='Create a config file with all possible config values.')
@click.option('--comments',
              is_flag=True,
              help='Add descriptions to the config.')
@click.option('--force', is_flag=True, help='Overwrite existing config.')
def cli_init(**kwargs):
    """Create a default config file."""
    from .init import init
    init(**kwargs)


@cli.command('create')
@common_options
@click.option('--force',
              is_flag=True,
              help='Overwrite existing run directories and IDS data.')
def cli_create(**kwargs):
    """Create the UQ run files."""
    from .create import create
    create(**kwargs)


@cli.command('submit')
@common_options
@click.option('--force', is_flag=True, help='Re-submit running jobs.')
def cli_submit(**kwargs):
    """Submit the UQ runs."""
    from .submit import submit
    submit(**kwargs)


@cli.command('status')
@common_options
@click.option('--detailed', is_flag=True, help='Detailed info on progress')
@click.option('--progress', is_flag=True, help='Fancy progress bar')
def cli_status(**kwargs):
    """Print the status of the UQ runs."""
    from .status import status
    status(**kwargs)


@cli.command('plot')
@click.option('-x', type=str, help='IDS of the x value')
@click.option('-y', type=str, help='IDS of the y value')
@click.option('-u',
              '--user',
              default=getuser(),
              type=str,
              help='User name, defaults to current user')
@click.option('-d',
              '--db',
              default='jet',
              type=str,
              help='Database or machine name')
@click.option('-r', '--run', type=int, help='Run number')
@click.option('-s', '--shot', type=int, help='Shot number')
@click.option('-i',
              '--inp',
              type=str,
              help='Input file, i.e. `data.csv` or `runs.yaml`')
@common_options
def cli_plot(**kwargs):
    """Plot some IDS data."""
    from .plot import plot
    plot(**kwargs)


@cli.command('clean')
@common_options
@click.option('--out', is_flag=True, help='Remove output data.')
@click.option('--force',
              is_flag=True,
              help='Overwrite backup file if necessary.')
def cli_clean(**kwargs):
    """Delete generated IDS data and the run dir."""
    from .cleanup import cleanup
    cleanup(**kwargs)


@cli.command('dash')
@common_options
def cli_dash(**kwargs):
    """Open dashboard for evaluating IDS data."""
    from .dash import dash
    dash(**kwargs)


if __name__ == '__main__':
    cli()
