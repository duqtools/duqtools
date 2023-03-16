import logging

import click

from ..cli import common_options, dry_run_option, logging_options, variables_option, yes_option
from ..operations import op_queue_context

logger = logging.getLogger(__name__)

try:
    import coverage
    coverage.process_startup()
except ImportError:
    pass


def cli_entry():
    from duqtools import fix_dependencies
    fix_dependencies()
    cli()


@click.group()
def cli(**kwargs):
    """For more information, check out the documentation:

    https://duqtools.readthedocs.io/large_scale_validation
    """


@cli.command('setup')
@click.option(
    '-i',
    '--input',
    'input_file',
    type=click.Path(exists=True),
    help='Input file, i.e. `data.csv` or `runs.yaml`',
    default='data.csv',
)
@click.option(
    '-t',
    '--template',
    'template_file',
    type=click.Path(exists=True),
    help='Template duqtools.yaml',
    default='duqtools.template.yaml',
)
@click.option('--force',
              is_flag=True,
              help='Overwrite existing run config directories')
@common_options(*logging_options, yes_option, dry_run_option)
def cli_setup(**kwargs):
    """Set up large scale validation."""
    from .setup import setup
    with op_queue_context():
        setup(**kwargs)


@cli.command('create')
@click.option('--force',
              is_flag=True,
              help='Overwrite existing run directories and IDS data.')
@common_options(*logging_options, yes_option, dry_run_option)
def cli_create(**kwargs):
    """Create data sets for large scale validation."""
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
@click.option('-s',
              '--status',
              'status_filter',
              type=str,
              multiple=True,
              help='Only submit jobs with this status.')
@click.option('-a', '--array', is_flag=True, help='Submit jobs as array.')
@common_options(*logging_options, yes_option, dry_run_option)
def cli_submit(**kwargs):
    """Submit large scale validation runs."""
    from .submit import submit
    with op_queue_context():
        submit(**kwargs)


@cli.command('status')
@click.option('--detailed', is_flag=True, help='Detailed info on progress')
@click.option('--progress', is_flag=True, help='Fancy progress bar')
@common_options(*logging_options)
def cli_status(**kwargs):
    """Check status large scale validation runs."""
    from .status import status
    with op_queue_context():
        status(**kwargs)


@cli.command('merge')
@click.option('--force', is_flag=True, help='Overwrite existing data')
@variables_option
@common_options(*logging_options, yes_option, dry_run_option)
def cli_merge(**kwargs):
    """Merge data sets with error propagation.

    By default, `duqduq merge` attempts to merge all known variables.
    Use `--variable` to select which variables to merge.
    """
    from .merge import merge
    with op_queue_context():
        merge(**kwargs)
