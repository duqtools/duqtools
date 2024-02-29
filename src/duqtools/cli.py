from __future__ import annotations

import functools
import logging
from datetime import datetime
from pathlib import Path
from sys import exit, stderr, stdout
from typing import Callable

import click
from pydantic import ValidationError

from ._click_opt_groups import GroupCmd, GroupOpt
from ._logging_utils import TermEscapeCodeFormatter, duqlog_screen, initialize_duqlog_screen
from .config import CFG, load_config
from .operations import op_queue, op_queue_context

logging.basicConfig(level=logging.INFO)
initialize_duqlog_screen()

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
                        help='Path to config.',
                        cls=GroupOpt,
                        group='Common options')(f)


def quiet_option(f):
    return click.option('-q',
                        '--quiet',
                        is_flag=True,
                        default=False,
                        help='Don\'t output anything to the screen'
                        ' (except mandatory prompts).',
                        cls=GroupOpt,
                        group='Common options')(f)


def debug_option(f):
    """Must be added together with `logfile_option`."""
    return click.option('--debug',
                        is_flag=True,
                        help='Enable debug print statements.',
                        cls=GroupOpt,
                        group='Common options')(f)


def dry_run_option(f):
    return click.option('--dry-run',
                        is_flag=True,
                        help='Execute without any side-effects.',
                        cls=GroupOpt,
                        group='Common options')(f)


def yes_option(f):
    return click.option('--yes',
                        is_flag=True,
                        help='Answer yes to questions automatically.',
                        cls=GroupOpt,
                        group='Common options')(f)


def logfile_option(f):
    """Must be added together with `debug_option`."""
    return click.option('--logfile',
                        '-l',
                        is_flag=False,
                        default='duqtools.log',
                        help='where to send the logfile,'
                        ' the special values stderr/stdout'
                        ' will send it there respectively.',
                        cls=GroupOpt,
                        group='Common options')(f)


logging_options = (logfile_option, debug_option)
all_options = (*logging_options, config_option, quiet_option, dry_run_option,
               yes_option)


def handles_option(f):
    return click.option('-h',
                        '--handle',
                        'handles',
                        type=str,
                        help='IMAS data handles.',
                        multiple=True)(f)


def variables_option(f):
    return click.option('-v',
                        '--variable',
                        'var_names',
                        type=str,
                        help='Name of the variables.',
                        multiple=True)(f)


def datafile_option(f):
    return click.option('-i',
                        '--input',
                        'input_files',
                        type=str,
                        help='Input file, i.e. `data.csv` or `runs.yaml`',
                        multiple=True)(f)


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

        start_time = datetime.now().astimezone().strftime(
            '%Y-%m-%d %H:%M:%S %z')
        logger.info('')
        logger.info(f'Duqtools starting at {start_time}')
        logger.info('------------------------------------------------')
        logger.info('')

    def parse_quiet(self, *, quiet, **kwargs):
        if quiet:
            duqlog_screen.handlers = []  # remove output methods
            CFG.quiet = True

    def parse_dry_run(self, *, dry_run, **kwargs):
        op_queue.dry_run = dry_run

    def parse_config(self, *, config, **kwargs):
        try:
            load_config(config)
        except ValidationError as e:
            exit(e)
        except FileNotFoundError as e:
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


def cli_entry(**kwargs):
    from duqtools import fix_dependencies
    fix_dependencies()
    cli()


@click.group()
def cli(**kwargs):
    """For more information, check out the documentation:

    https://duqtools.readthedocs.io
    """
    pass


@cli.command('init', cls=GroupCmd)
@click.option('-o',
              '--out',
              'out_file',
              help='Path to write config to (default=duqtools.yaml).',
              default='duqtools.yaml')
@click.option('--force', is_flag=True, help='Overwrite existing config.')
@common_options(*logging_options, quiet_option, dry_run_option, yes_option)
def cli_init(**kwargs):
    """Create a default config file."""
    from .init import init
    with op_queue_context():
        try:
            init(**kwargs)
        except RuntimeError as e:
            exit(e)


@cli.command('setup')
@click.option(
    '-r',
    '--run_name',
    type=str,
    help='Name of the run.',
    default='duqtools',
)
@click.option(
    '-t',
    '--template',
    'template_file',
    type=click.Path(exists=True),
    help='Template duqtools.yaml',
    default='duqtools.template.yaml',
)
@click.option('-h', '--handle', 'handle', type=str, help='IMAS data handle.')
@click.option('--force', is_flag=True, help='Overwrite existing config')
@common_options(*logging_options, yes_option)
def cli_setup(**kwargs):
    """Template substitution for duqtools config."""
    from .setup import setup
    with op_queue_context():
        setup(**kwargs)


@cli.command('create', cls=GroupCmd)
@click.option('--force',
              is_flag=True,
              help='Overwrite existing run directories and IDS data.')
@click.option('--no-sampling',
              is_flag=True,
              help='Create base run (ignores `dimensions`/`sampler`).')
@common_options(*all_options)
def cli_create(**kwargs):
    """Read duqtools.yaml and create the new IMAS data files from template
    data."""
    from .create import create
    with op_queue_context():
        create(cfg=CFG, **kwargs)


@cli.command('recreate', cls=GroupCmd)
@click.argument('runs', type=Path, nargs=-1)
@common_options(*all_options)
def cli_recreate(**kwargs):
    """Read `runs.yaml` and re-create the given runs.

    \b
    Example:

    - `duqtools recreate run_0003 run_0004 --force`
    """
    from .create import recreate
    with op_queue_context():
        recreate(cfg=CFG, **kwargs)


@cli.command('submit', cls=GroupCmd)
@click.option('--force',
              is_flag=True,
              help='Re-submit running or completed jobs.')
@click.option('--schedule',
              is_flag=True,
              help=('Schedule and submit jobs automatically.'))
@click.option('-j',
              '--max_jobs',
              type=int,
              help='Maximum number of jobs running simultaneously.',
              default=10)
@click.option(
    '--max_array_size',
    type=int,
    default=100,
    help='Maximum array size for slurm (usually 1001, default = 100).')
@click.option('-a', '--array', is_flag=True, help=('Submit jobs as array. '))
@click.option('--array-script',
              is_flag=True,
              help=('Create script to submit jobs as array. '
                    'Like --array, but does not submit.'))
@click.option('--limit',
              type=int,
              help=('Limits total number of jobs to submit.'))
@click.option('-r',
              '--resubmit',
              multiple=True,
              default=tuple(),
              type=Path,
              help='Case to re-submit, can be specified multiple times')
@click.option('-s',
              '--status',
              'status_filter',
              type=str,
              multiple=True,
              help='Only submit jobs with this status.')
@common_options(*all_options)
def cli_submit(**kwargs):
    """Submit system runs to job management system.

    This subcommand will read `runs.yaml`, and start all runs which are
    not yet running. By default, It will not re-submit running or
    finished jobs.

    There is a scheduler that will continue to submit jobs until the
    specified maximum number of jobs is running. Once a job has
    completed, a new job will be submitted from the queue to fill the
    spot.
    """
    from .submit import submit
    with op_queue_context():
        submit(cfg=CFG, **kwargs)


@cli.command('sync_prominence', cls=GroupCmd)
@click.option('--force', is_flag=True, help='Overwrite data if necessary')
@common_options(*all_options)
def cli_sync_prominence(**kwargs):
    """Sync data back from prominence.

    This subcommand is meant to be used in combination with the
    prominence submission system. After the jobs are completed on
    prominence this command can be used to retrieve and extract the
    completed runs from prominence to the local machine, so that they
    can be used in further analysis.
    """
    from .sync_prominence import sync_prominence
    with op_queue_context():
        sync_prominence(cfg=CFG, **kwargs)


@cli.command('status', cls=GroupCmd)
@click.option('--detailed', is_flag=True, help='Detailed info on progress')
@click.option('--progress', is_flag=True, help='Fancy progress bar')
@common_options(*all_options)
def cli_status(**kwargs):
    """Print the status of the system runs."""
    from .status import status
    status(cfg=CFG, **kwargs)


@cli.command('plot')
@handles_option
@variables_option
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
@datafile_option
@common_options(*logging_options)
def cli_plot(**kwargs):
    """Generate plots for IMAS data.

    \b
    Examples:

    - `duqtools plot -v t_i_ave -v zeff -i data.csv`
    - `duqtools plot -v t_i_ave -v zeff -h user/jet/91234/5`
    - `duqtools plot -v zeff -h db/91234/5 -h db/91234/6 -h db/91234/7`
    - `duqtools plot -v zeff -h db/91234/5 -i data.csv`
    - `duqtools plot -v zeff -h db/91234/5 -o json`
    """
    from .plot import plot
    plot(**kwargs)


@cli.command('clean', cls=GroupCmd)
@click.option('--out', is_flag=True, help='Remove output data.')
@click.option('--force',
              is_flag=True,
              help='Overwrite backup file if necessary.')
@common_options(*all_options)
def cli_clean(**kwargs):
    """Delete generated IDS data and the run dir."""
    from .cleanup import cleanup
    with op_queue_context():
        cleanup(cfg=CFG, **kwargs)


@cli.command('go', cls=GroupCmd)
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
        create(cfg=CFG, **kwargs)
    with op_queue_context():
        submit(cfg=CFG,
               max_jobs=None,
               array=True,
               schedule=None,
               resubmit=tuple(),
               **kwargs)

    skwargs = kwargs.copy()
    skwargs['detailed'] = True
    skwargs['progress'] = False
    status(cfg=CFG, **skwargs)

    dash(**kwargs)


@cli.command('yolo')
@click.pass_context
def cli_yolo(ctx, **kwargs):
    """Live on the edge, run `duqtools go --force --yes --quiet`."""
    ctx.invoke(cli_go, force=True, quiet=True, yes=True)


@cli.command('dash', cls=GroupCmd)
@common_options(*logging_options, quiet_option, dry_run_option, yes_option)
def cli_dash(**kwargs):
    """Open dashboard for evaluating IDS data."""
    from .dash import dash
    dash(**kwargs)


@cli.command('merge', cls=GroupCmd)
@handles_option
@variables_option
@click.option('-t',
              '--template',
              required=True,
              type=str,
              help='IMAS location to use as the template for the target')
@click.option('-o',
              '--out',
              'target',
              required=True,
              type=str,
              help='IMAS location to store the result in')
@datafile_option
@click.option('--force',
              is_flag=True,
              help='Overwrite existing output dataset.')
@common_options(*all_options)
def cli_merge(**kwargs):
    """Merge data sets with error propagation.

    Example Merging two IDSes. Run number `8000` is the template.
    Only The `t_e` variable is merged.

    The resulting IDS is saved to your own test database with
    shot number `36982` and run number `9999`.

    Example:

    \b
    ```
    duqtools merge \\
        -t g2jcitri/aug/36982/8000 \\
        -o test/36982/9999 \\
        -h g2jcitri/aug/36982/8001 \\
        -h g2jcitri/aug/36982/8000 \\
        -v t_e
    ```
    \f
    Note:

    The `-t`, `-o` and `-h` options expect an IMAS path formatted as
    `user/db/shot/number` or `db/shot/number`.

    By default, `duqduq merge` attempts to merge all known variables.
    Use `--variable` to select which variables to merge.
    """
    from .merge import merge
    with op_queue_context():
        merge(**kwargs)


@cli.command('list-variables')
@config_option
def cli_list_variables(config, **kwargs):
    """List available variables.

    This also picks up variables from `duqtools.yaml` if it exists in the local
    directory.
    """
    from .list_variables import list_variables
    try:
        cfg = load_config(config)
    except FileNotFoundError:
        print(f'Cannot find `{config}`.')
        cfg = CFG
    list_variables(cfg=cfg, **kwargs)


@cli.command('version')
def cli_version(**kwargs):
    """Print the version and exit."""
    import git

    from duqtools import __version__

    string = f'duqtools {__version__}'

    try:
        repo = git.Repo(Path(__file__), search_parent_directories=True)
        sha = repo.head.object.hexsha
    except BaseException:
        sha = '???'

    string += f' (rev: {sha})'

    click.echo(string)


if __name__ == '__main__':
    cli()
