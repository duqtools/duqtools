import logging

import click

logger = logging.getLogger(__name__)

try:
    import coverage
    coverage.process_startup()
except ImportError:
    pass


def cli_entry():
    from duqtools import fix_dependencies
    fix_dependencies()
    click.secho(
        'Note: This tool is a work in progress and not ready to be used.',
        bold=True,
        bg='red',
        fg='white')
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
)
@click.option(
    '-t',
    '--template',
    'template_file',
    type=click.Path(exists=True),
    help='Template duqtools.yaml',
    default='duqtools.template.yaml',
)
@click.option(
    '-r',
    '--runs',
    'runs_dir',
    type=click.Path(),
    help='Output directory for created runs',
    default='duqduq',
)
def cli_setup(**kwargs):
    """Set up large scale validation."""
    from .setup import setup
    setup(**kwargs)


@cli.command('create')
def cli_create(**kwargs):
    """Create data sets for large scale validation."""
    from .create import create
    create(**kwargs)


@cli.command('merge')
def cli_merge(**kwargs):
    """Merge large scale validation data."""
    from .merge import merge
    merge(**kwargs)
