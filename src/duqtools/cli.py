import logging
from datetime import datetime
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

    def callback(ctx, param, config):
        if ctx.command.name != 'init':
            try:
                cfg.parse_file(config)
            except ValidationError as e:
                exit(e)

        return config

    return click.option('-c',
                        '--config',
                        default='duqtools.yaml',
                        help='Path to config.',
                        callback=callback,
                        is_eager=True)(f)


def quiet_option(f):

    def callback(ctx, param, quiet):
        if quiet:
            duqlog_screen.handlers = []  # remove output methods
            cfg.quiet = True

        return quiet

    return click.option('-q',
                        '--quiet',
                        is_flag=True,
                        default=False,
                        help='Don\'t output anything to the screen'
                        ' (except mandatory prompts).',
                        callback=callback)(f)


def debug_option(f):

    def callback(ctx, param, debug):
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            for handle in logging.getLogger().handlers:
                handle.setLevel(logging.DEBUG)

        return debug

    return click.option('--debug',
                        is_flag=True,
                        help='Enable debug print statements.',
                        callback=callback,
                        is_eager=True)(f)


def dry_run_option(f):

    def callback(ctx, param, dry_run):
        if dry_run:
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
        level = logging.getLogger().handlers[0].level
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

        return logfile

    return click.option('--logfile',
                        '-l',
                        is_flag=False,
                        default='duqtools.log',
                        help='where to send the logfile,'
                        ' the special values stderr/stdout'
                        ' will send it there respectively.',
                        callback=callback,
                        is_eager=True)(f)


def common_options(func):
    """common_options.

    IMPORTANT: wrappers can be executed in any order, determined by
    the order of options on the command line
    This means that sometimes the order of arguments matters,
    specifically for stuff like debug flags.

    We can control this a bit with the is_eager flag, currently is_eager are:
    - debug_option
    - config_option
    - logfile_option

    Ideally we can determine the full order of processing, but this requires us
    to only have the options set a flag, and then do the processing afterwards
    in a different wrapper
    """
    for wrapper in (logfile_option, debug_option, config_option, quiet_option,
                    dry_run_option, yes_option):
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
    with op_queue_context():
        try:
            init(**kwargs)
        except RuntimeError as e:
            exit(e)


@cli.command('create')
@common_options
@click.option('--force',
              is_flag=True,
              help='Overwrite existing run directories and IDS data.')
def cli_create(**kwargs):
    """Create the UQ run files."""
    from .create import create
    with op_queue_context():
        create(**kwargs)


@cli.command('submit')
@common_options
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
@common_options
@click.option('--detailed', is_flag=True, help='Detailed info on progress')
@click.option('--progress', is_flag=True, help='Fancy progress bar')
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
    with op_queue_context():
        cleanup(**kwargs)


@cli.command('go')
@common_options
@click.option('--force', is_flag=True, help='Overwrite files when necessary.')
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


if __name__ == '__main__':
    cli()
