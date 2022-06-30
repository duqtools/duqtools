import logging

import click
import coverage

from duqtools.config import cfg

logger = logging.getLogger(__name__)
coverage.process_startup()


@click.group()
@click.option('-c',
              '--config',
              default='duqtools.yaml',
              help='Path to config.')
@click.option('--debug', is_flag=True, help='Enable debug print statements.')
@click.pass_context
def cli(ctx, config='duqtools.yaml', debug=False, **kwargs):
    """For more information, check out the documentation:

    https://duqtools.readthedocs.io
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.debug('Params: %s', ctx.params)
    logger.debug('Subcommand: %s', ctx.invoked_subcommand)

    if ctx.invoked_subcommand != 'init':
        cfg.parse_file(config)


@cli.command('init')
@click.option('--full',
              is_flag=True,
              help='Create a config file with all possible config values.')
@click.option('--force', is_flag=True, help='Overwrite existing config.')
def cli_init(**kwargs):
    """Create a default config file."""
    from .init import init
    init(**kwargs)


@cli.command('create')
@click.option('--force',
              is_flag=True,
              help='Overwrite existing run directories and IDS data.')
def cli_create(**kwargs):
    """Create the UQ run files."""
    from .create import create
    create(**kwargs)


@cli.command('submit')
@click.option('--force', is_flag=True, help='Re-submit running jobs.')
def cli_submit(**kwargs):
    """Submit the UQ runs."""
    from .submit import submit
    submit(**kwargs)


@cli.command('status')
@click.option('--detailed', is_flag=True, help='Detailed info on progress')
@click.option('--progress', is_flag=True, help='Fancy progress bar')
def cli_status(**kwargs):
    """Print the status of the UQ runs."""
    from .status import status
    status(**kwargs)


@cli.command('plot')
def cli_plot(**kwargs):
    """Analyze the results and generate a report'."""
    from .plot import plot
    plot(**kwargs)


@cli.command('clean')
@click.option('--out', is_flag=True, help='Remove output data.')
def cli_clean(**kwargs):
    """Delete generated IDS data and the run dir."""
    from .cleanup import cleanup
    cleanup(**kwargs)


@cli.command('dash')
def cli_dash(**kwargs):
    """Open dashboard for evaluating IDS data."""
    from .dash import dash
    dash(**kwargs)


if __name__ == '__main__':
    cli()
