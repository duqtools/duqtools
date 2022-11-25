import functools
import logging
from datetime import datetime
from pathlib import Path
from sys import exit, stderr, stdout
from typing import Callable

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
    """Must be added together with `logfile_option`."""
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
    """Must be added together with `debug_option`."""
    return click.option('--logfile',
                        '-l',
                        is_flag=False,
                        default='duqtools.log',
                        help='where to send the logfile,'
                        ' the special values stderr/stdout'
                        ' will send it there respectively.')(f)


all_options = (logfile_option, debug_option, config_option, quiet_option,
               dry_run_option, yes_option)


class OptionParser:

    def wrap(self, func: Callable):
        """With this wrapper it becomes possible to parse common options in
        user defined order."""

        def callback(**kwargs):
            for parse in (
                    self.parse_config,
                    self.parse_logfile,
                    self.parse_yes,
                    self.parse_dry_run,
                    self.parse_quiet,
            ):
                try:
                    parse(**kwargs)
                except TypeError:
                    # Skip when option has not been set
                    pass
            func(**kwargs)

        return callback

    def parse_logfile(self, *, logfile, debug, **kwargs):
        level = logging.DEBUG if debug else logging.INFO

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

    def parse_quiet(self, *, quiet, **kwargs):
        if quiet:
            duqlog_screen.handlers = []  # remove output methods
            cfg.quiet = True

    def parse_dry_run(self, *, dry_run, **kwargs):
        op_queue.dry_run = dry_run

    def parse_config(self, *, config, **kwargs):
        try:
            cfg.parse_file(config)
        except ValidationError as e:
            exit(e)

    def parse_yes(self, *, yes, **kwargs):
        op_queue.yes = yes


def common_options(*options):
    """common_options.

    IMPORTANT: This must be the last click option specified before
    the execution of the actual function, otherwise options will be
    missing
    """

    def decorator(func):
        wrapper = OptionParser().wrap(func)

        for option in options:
            wrapper = option(wrapper)

        functools.update_wrapper(wrapper, func)

        return wrapper

    return decorator


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
@click.option('-o',
              '--out',
              'out_file',
              help='Path to write config to (default=duqtools.yaml).',
              default='duqtools.yaml')
@click.option('--force', is_flag=True, help='Overwrite existing config.')
@common_options(logfile_option, debug_option, quiet_option, dry_run_option,
                yes_option)
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
@common_options(*all_options)
def cli_create(**kwargs):
    """Create the UQ run files."""
    from .create import create
    with op_queue_context():
        create(**kwargs)


@cli.command('recreate')
@click.argument('runs', type=Path, nargs=-1)
@common_options(*all_options)
def cli_recreate(**kwargs):
    """Read `runs.yaml` and re-create the given runs.

    Example:
    \b
    - duqtools recreate run_0003 run_0004 --force
    """
    from .create import recreate
    with op_queue_context():
        recreate(**kwargs)


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
@common_options(*all_options)
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
@common_options(*all_options)
def cli_status(**kwargs):
    """Print the status of the UQ runs."""
    from .status import status
    status(**kwargs)


@cli.command('plot')
@click.option('-v',
              '--variables',
              'var_names',
              type=str,
              help='Name of the variables to plot',
              multiple=True)
@click.option('-m',
              '--imas',
              'imas_paths',
              type=str,
              help='IMAS path formatted as <user>/<db>/<shot>/<number>.',
              multiple=True)
@click.option('-u', '--user', 'user', type=str, help='IMAS user.')
@click.option('-d', '--db', 'db', type=str, help='IMAS database.')
@click.option('-s', '--shot', 'shot', type=int, help='IMAS shot.')
@click.option('-r',
              '--runs',
              'runs',
              type=int,
              multiple=True,
              help='IMAS run (multiple runs can be specified)')
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
@click.option('-e',
              '--errorbars',
              is_flag=True,
              help='Plot the errorbars (if present)')
def cli_plot(**kwargs):
    """Plot some IDS data.

    \b
    Examples:
    - duqtools plot -v t_i_ave -v zeff -i data.csv
    - duqtools plot -v t_i_ave -v zeff -m jet/91234/5
    - duqtools plot -v zeff -u user -d jet -s 91234 -r 5 -r 6 -r 7
    - duqtools plot -v zeff -m user/91234/5 -i data.csv
    - duqtools plot -v zeff -m user/91234/5 -o json
    """
    from .plot import plot
    plot(**kwargs)


@cli.command('clean')
@click.option('--out', is_flag=True, help='Remove output data.')
@click.option('--force',
              is_flag=True,
              help='Overwrite backup file if necessary.')
@common_options(*all_options)
def cli_clean(**kwargs):
    """Delete generated IDS data and the run dir."""
    from .cleanup import cleanup
    with op_queue_context():
        cleanup(**kwargs)


@cli.command('go')
@click.option('--force', is_flag=True, help='Overwrite files when necessary.')
@common_options(*all_options)
def cli_go(**kwargs):
    """Run create, submit, status, dash in succession.

    Useful for existing tested and working pipelines.
    """
    from .create import create
    from .dash import dash
    from .status import status
    from .submit import submit
    with op_queue_context():
        create(**kwargs)
    with op_queue_context():
        submit(max_jobs=None,
               array=True,
               schedule=None,
               resubmit=tuple(),
               **kwargs)

    skwargs = kwargs.copy()
    skwargs['detailed'] = True
    skwargs['progress'] = False
    status(**skwargs)

    dash(**kwargs)


@cli.command('yolo')
@click.pass_context
def cli_yolo(ctx, **kwargs):
    """Live on the edge, run `duqtools go --force --yes --quiet`."""
    ctx.invoke(cli_go, force=True, quiet=True, yes=True)


@cli.command('dash')
@common_options(*all_options)
def cli_dash(**kwargs):
    """Open dashboard for evaluating IDS data."""
    from .dash import dash
    dash(**kwargs)


@cli.command('merge')
@click.option('-t',
              '--template',
              required=True,
              type=str,
              help='IMAS location to use as the template for the target')
@click.option('-o',
              '--output',
              'target',
              required=True,
              type=str,
              help='IMAS location to store the result in')
@click.option('-h',
              '--handle',
              'handles',
              type=str,
              help='handles to merge to the target',
              multiple=True)
@click.option('-v',
              '--variable',
              'variables',
              type=str,
              help='variables to merge to the target',
              multiple=True)
@click.option('--all',
              'merge_all',
              is_flag=True,
              help='Try to merge all known variables.')
@click.option('-i',
              '--input',
              'input_files',
              type=str,
              help='Input file, i.e. `data.csv` or `runs.yaml`',
              multiple=True)
@common_options(*all_options)
def cli_merge(**kwargs):
    """Merge data sets with error propagation.

    Example Merging two IDSes. Run number `8000` is the template.
    Only The `t_e` variable is merged.
    The resulting IDS is saved to your own test database with
    shot number `36982` and run number `9999`

    > duqtools merge -t g2jcitri/aug/36982/8000 -o test/36982/9999 \
            -h g2jcitri/aug/36982/8001 -h g2jcitri/aug/36982/8000 -v t_e

    Note:

    The -t -T and -h options expect an IMAS path formatted as
    `user/db/shot/number`
    """
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
