import functools
import logging
from datetime import datetime
from pathlib import Path
from sys import exit, stderr, stdout

import click
from pydantic import ValidationError

from ._logging_utils import TermEscapeCodeFormatter, duqlog_screen
from .config import cfg
from .operations import op_queue, op_queue_context

logger = logging.getLogger(__name__)

try:
    import coverage
    coverage.process_startup()
except ImportError:
    pass


def config_option(f):
    return click.option('-c',
                        '--config',
                        default='duqtools.yaml',
                        help='Path to config.')(f)


def quiet_option(f):
    return click.option('-q',
                        '--quiet',
                        is_flag=True,
                        default=False,
                        help='Don\'t output anything to the screen'
                        ' (except mandatory prompts).')(f)


def debug_option(f):
    return click.option('--debug',
                        is_flag=True,
                        help='Enable debug print statements.')(f)


def dry_run_option(f):
    return click.option('--dry-run',
                        is_flag=True,
                        help='Execute without any side-effects.')(f)


def yes_option(f):
    return click.option('--yes',
                        is_flag=True,
                        help='Answer yes to questions automatically.')(f)


def logfile_option(f):
    return click.option('--logfile',
                        '-l',
                        is_flag=False,
                        default='duqtools.log',
                        help='where to send the logfile,'
                        ' the special values stderr/stdout'
                        ' will send it there respectively.')(f)


def parse_common_options(func):
    """With this function it becomes possible to parse the options in user
    defined order."""

    def parse_options(ctx, *, logfile, debug, quiet, dry_run, config, yes,
                      **kwargs):
        # Config option
        if ctx.command.name != 'init':
            try:
                cfg.parse_file(config)
            except ValidationError as e:
                exit(e)

        # Debug option
        if debug:
            level = logging.DEBUG
        else:
            level = logging.INFO

        # Logfile option
        streams = {'stdout': stdout, 'stderr': stderr}
        logging.getLogger().handlers = []

        if logfile in streams.keys():
            logging.basicConfig(stream=streams[logfile], level=level)
        else:
            fhandler = logging.FileHandler(logfile)
            fhandler.setLevel(level)

            # Remove fancies from logfiles
            escaped_format = TermEscapeCodeFormatter(logging.BASIC_FORMAT)
            fhandler.setFormatter(escaped_format)
            logging.getLogger().addHandler(fhandler)

        logger.info('')
        logger.info(
            'Duqtools starting at '
            f'{datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")}')
        logger.info('------------------------------------------------')
        logger.info('')

        # Yes option
        op_queue.yes = yes

        # Dry run option
        op_queue.dry_run = dry_run

        # Quiet option
        if quiet:
            duqlog_screen.handlers = []  # remove output methods
            cfg.quiet = True

    def callback(ctx, **kwargs):
        parse_options(ctx, **kwargs)
        func(**kwargs)

    return callback


def common_options(func):
    """common_options.

    IMPORTANT: This must be the last click option specified before
    the execution of the actual function, otherwise options will be
    missing
    """
    wrapper = click.pass_context(parse_common_options(func))

    for option in (logfile_option, debug_option, config_option, quiet_option,
                   dry_run_option, yes_option):
        wrapper = option(wrapper)

    functools.update_wrapper(wrapper, func)

    return wrapper


def cli_entry():
    from duqtools import fix_dependencies
    fix_dependencies()
    cli()


@click.group()
def cli(**kwargs):
    """For more information, check out the documentation:

    https://duqtools.readthedocs.io
    """
    pass


@cli.command('init')
@click.option('--force', is_flag=True, help='Overwrite existing config.')
@common_options
def cli_init(**kwargs):
    """Create a default config file."""
    from .init import init
    with op_queue_context():
        try:
            init(**kwargs)
        except RuntimeError as e:
            exit(e)


@cli.command('create')
@click.option('--force',
              is_flag=True,
              help='Overwrite existing run directories and IDS data.')
@common_options
def cli_create(**kwargs):
    """Create the UQ run files."""
    from .create import create
    with op_queue_context():
        create(**kwargs)


@cli.command('submit')
@click.option('--force',
              is_flag=True,
              help='Re-submit running or completed jobs.')
@click.option(
    '--schedule',
    is_flag=True,
    help='Schedule and submit jobs automatically. `max_jobs` must be defined.')
@click.option('-j',
              '--max_jobs',
              type=int,
              help='Maximum number of jobs to submit.')
@click.option('-a', '--array', is_flag=True, help='Submit jobs as array.')
@click.option('-r',
              '--resubmit',
              multiple=True,
              default=tuple(),
              type=Path,
              help='Case to re-submit, can be specified multiple times')
@common_options
def cli_submit(**kwargs):
    """Submit the UQ runs.

    This subcommand will read `runs.yaml`, and start all runs which are not yet
    running. By default, It will not re-submit running or finished jobs.

    There is a scheduler that will continue to submit jobs until the specified
    maximum number of jobs is running. Once a job has completed, a new job will
    be submitted from the queue to fill the spot.
    """
    from .submit import submit
    with op_queue_context():
        submit(**kwargs)


@cli.command('status')
@click.option('--detailed', is_flag=True, help='Detailed info on progress')
@click.option('--progress', is_flag=True, help='Fancy progress bar')
@common_options
def cli_status(**kwargs):
    """Print the status of the UQ runs."""
    from .status import status
    status(**kwargs)


@cli.command('plot')
@click.option('-x',
              'x_path',
              default='profiles_1d/*/grid/rho_tor_norm',
              type=str,
              help='IDS of the x value')
@click.option('-y',
              'y_paths',
              type=str,
              help='IDS of the y value',
              multiple=True)
@click.option('-m',
              '--imas',
              'imas_paths',
              type=str,
              help='IMAS path formatted as <user>/<db>/<shot>/<number>.',
              multiple=True)
@click.option('-d',
              '--ids',
              type=str,
              default='core_profiles',
              help='Which IDS to grab data from')
@click.option('-i',
              '--input',
              'input_files',
              type=str,
              help='Input file, i.e. `data.csv` or `runs.yaml`',
              multiple=True)
@click.option('-o',
              '--format',
              'extensions',
              type=str,
              help='Output format (json, html, png, svg, pdf), default: html.',
              default=('html', ),
              multiple=True)
@common_options
def cli_plot(**kwargs):
    """Plot some IDS data."""
    from .plot import plot
    with op_queue_context():
        plot(**kwargs)


@cli.command('clean')
@click.option('--out', is_flag=True, help='Remove output data.')
@click.option('--force',
              is_flag=True,
              help='Overwrite backup file if necessary.')
@common_options
def cli_clean(**kwargs):
    """Delete generated IDS data and the run dir."""
    from .cleanup import cleanup
    with op_queue_context():
        cleanup(**kwargs)


@cli.command('go')
@click.option('--force', is_flag=True, help='Overwrite files when necessary.')
@common_options
def cli_go(**kwargs):
    """Run create - submit - status - dash in succession, very useful for
    existing tested and working pipelines
    """
    from .create import create
    from .dash import dash
    from .status import status
    from .submit import submit
    with op_queue_context():
        create(**kwargs)
    with op_queue_context():
        submit(**kwargs)

    skwargs = kwargs.copy()
    skwargs['detailed'] = True
    skwargs['progress'] = False
    status(**skwargs)

    dash(**kwargs)


@cli.command('dash')
@common_options
def cli_dash(**kwargs):
    """Open dashboard for evaluating IDS data."""
    from .dash import dash
    dash(**kwargs)


@cli.command('merge')
@common_options
def cli_merge(**kwargs):
    """Merge data sets with error propagation."""
    from .merge import merge
    with op_queue_context():
        merge(**kwargs)


@cli.command('list-variables')
@config_option
def cli_list_variables(**kwargs):
    """List available variables.

    Picks up variables from `duqtools.yaml` if it exists in the local
    directory.
    """
    from .list_variables import list_variables
    list_variables(**kwargs)


if __name__ == '__main__':
    cli()
