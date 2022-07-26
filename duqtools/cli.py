import logging
from datetime import datetime
from sys import stderr, stdout

import click
import coverage

from .config import cfg
from .operations import op_queue

logger = logging.getLogger(__name__)
coverage.process_startup()


def config_option(f):

    def callback(ctx, param, config):
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
            op_queue.dry_run = True
        else:
            op_queue.dry_run = False

        return dry_run

    return click.option('--dry-run',
                        is_flag=True,
                        help='Execute without any side-effects.',
                        callback=callback)(f)


def yes_option(f):

    def callback(ctx, param, yes):
        if yes:
            logger.info('--yes enabled')
            op_queue.yes = True
        else:
            op_queue.yes = False
        return yes

    return click.option('--yes',
                        is_flag=True,
                        help='Answer yes to questions automatically.',
                        callback=callback)(f)


def logfile_option(f):

    def callback(ctx, param, logfile):
        streams = {'stdout': stdout, 'stderr': stderr}

        logger.info(f'logging to {logfile}')
        logging.getLogger().handlers = []

        if logfile in streams.keys():
            logging.basicConfig(stream=streams[logfile], level=logging.INFO)
        else:
            logging.basicConfig(filename=logfile, level=logging.INFO)

        logger.info('')
        logger.info(
            'Duqtools starting at '
            f'{datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")}')
        logger.info('------------------------------------------------')
        logger.info('')

        return logfile

    return click.option('--logfile',
                        '-l',
                        is_flag=False,
                        default='duqtools.log',
                        help='where to send the logfile,'
                        ' the special values stderr/stdout'
                        ' will send it there respectively.',
                        callback=callback)(f)


def common_options(func):
    for wrapper in (logfile_option, debug_option, config_option,
                    dry_run_option, yes_option):
        # config_option MUST BE BEFORE dry_run_option
        # logfile_option must be before debug_option
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
@click.option('-x', 'x_val', type=str, help='IDS of the x value')
@click.option('-y',
              'y_vals',
              type=str,
              help='IDS of the y value',
              multiple=True)
@click.option('-m',
              '--imas',
              'imas_paths',
              type=str,
              help='IMAS path formatted as <user>/<db>/<shot>/<number>.',
              multiple=True)
@click.option('-i',
              '--input',
              'input_files',
              type=str,
              help='Input file, i.e. `data.csv` or `runs.yaml`',
              multiple=True)
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
