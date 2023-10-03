from __future__ import annotations

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
@click.option('-o', '--output', type=str, help='Output subdirectory')
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
@click.option(
    '-p',
    '--pattern',
    type=str,
    help=
    'Only create data for configs in subdirectories matching this glob pattern.'
)
@click.option(
    '-i',
    '--input',
    'input_file',
    type=str,
    help=
    'Only create data for configs where `template_data` matches a handle in this data.csv.'
)
@click.option('--no-sampling',
              is_flag=True,
              help='Create base runs (ignores `dimensions`/`sampler`).')
@common_options(*logging_options, yes_option, dry_run_option)
def cli_create(**kwargs):
    """Create data sets for large scale validation.

    Example to only match config files in subdirectories matching jet*:
    `duqduq create --pattern 'jet*/**'`
    """
    from .create import create
    with op_queue_context():
        create(**kwargs)


@cli.command('submit')
@click.option('--force',
              is_flag=True,
              help='Re-submit running or completed jobs.')
@click.option('--schedule',
              is_flag=True,
              help=('Schedule and submit jobs automatically. '))
@click.option('-j',
              '--max_jobs',
              type=int,
              help='Maximum number of jobs running simultaneously.',
              default=10)
@click.option('-s',
              '--status',
              'status_filter',
              type=str,
              multiple=True,
              help='Only submit jobs with this status.')
@click.option(
    '-p',
    '--pattern',
    type=str,
    help=
    'Only submit jobs for runs in subdirectories matching this glob pattern.')
@click.option(
    '-i',
    '--input',
    'input_file',
    type=str,
    help=
    'Only submit jobs for configs where `template_data` matches a handle in this data.csv.'
)
@click.option('-a', '--array', is_flag=True, help=('Submit jobs as array. '))
@click.option('--array-script',
              is_flag=True,
              help=('Create script to submit jobs as array. '
                    'Like --array, but does not submit.'))
@click.option('--limit',
              type=int,
              help=('Limits total number of jobs to submit.'))
@click.option(
    '--max_array_size',
    type=int,
    default=100,
    help='Maximum array size for slurm (usually 1001, default = 100).')
@common_options(*logging_options, yes_option, dry_run_option)
def cli_submit(**kwargs):
    """Submit large scale validation runs."""
    from .submit import submit
    with op_queue_context():
        submit(**kwargs)


@cli.command('status')
@click.option('--detailed', is_flag=True, help='Detailed info on progress')
@click.option('--progress', is_flag=True, help='Fancy progress bar')
@click.option(
    '-p',
    '--pattern',
    type=str,
    help=
    'Show status only for runs in subdirectories matching this glob pattern.')
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
