import logging
from pathlib import Path
from typing import Iterable

import click
import pandas as pd

from .apply_model import apply_model
from .config import cfg
from .ids import ImasHandle
from .matrix_samplers import get_matrix_sampler
from .models import WorkDirectory
from .operations import add_to_op_queue, op_queue
from .schema.runs import Runs
from .system import get_system

logger = logging.getLogger(__name__)

RUN_PREFIX = 'run_'


def any_locations_exist(locations: Iterable[ImasHandle]):
    """Check IDS coordinates and raise if any exist."""
    any_exists = False
    for location in locations:
        if location.exists():
            logger.info('Target %s already exists', location)
            op_queue.add(action=lambda: None,
                         description=click.style('Not creating IDS',
                                                 fg='red',
                                                 bold=True),
                         extra_description=f'IDS entry {location} exists')
            any_exists = True
    if any_exists:
        return True
    return False


@add_to_op_queue('Setting inital condition of', '{target_in}', quiet=True)
def apply_combination(target_in: ImasHandle, run_dir: Path,
                      combination) -> None:
    for model in combination:
        apply_model(model, run_dir=run_dir, ids_mapping=target_in)


@add_to_op_queue('Writing runs', '{workspace.runs_yaml}', quiet=True)
def write_runs_file(runs: list, workspace) -> None:
    runs = Runs.parse_obj(runs)
    with open(workspace.runs_yaml, 'w') as f:
        runs.yaml(stream=f)


@add_to_op_queue('Writing csv', quiet=True)
def write_runs_csv(runs, fname: str = 'data.csv'):
    run_map = {run['dirname']: run['data_out'].dict() for run in runs}
    df = pd.DataFrame.from_dict(run_map, orient='index')
    df.to_csv(fname)


def create(*, force, **kwargs):
    """Create input for jetto and IDS data structures.

    Parameters
    ----------
    force : bool
        Override protection if data and directories already exist.
    **kwargs
        Unused.
    """
    options = cfg.create

    if not options:
        logger.warning('No create options specified.')
        return

    workspace = WorkDirectory.parse_obj(cfg.workspace)

    template_drc = options.template
    dimensions = options.dimensions
    matrix_sampler = get_matrix_sampler(options.sampler.method)

    system = get_system()

    if not options.template_data:
        source = system.imas_from_path(template_drc)
    else:
        source = ImasHandle.parse_obj(options.template_data)

    logger.info('Source data: %s', source)
    matrix = tuple(model.expand() for model in dimensions)
    combinations = matrix_sampler(*matrix, **dict(options.sampler))

    # Safety checks

    targets_exist = False
    if not force:
        if workspace.runs_yaml.exists():
            op_queue.add(action=lambda: None,
                         description=click.style('Not creating runs.yaml',
                                                 fg='red',
                                                 bold=True),
                         extra_description=f'{workspace.runs_yaml} exists')
            targets_exist = True

        locations = (ImasHandle(db=options.data.imasdb,
                                shot=source.shot,
                                run=options.data.run_in_start_at + i)
                     for i in range(len(combinations)))

        if any_locations_exist(locations):
            targets_exist = True

    runs = []

    if not force:
        for i in range(len(combinations)):
            run_name = f'{RUN_PREFIX}{i:04d}'
            run_drc = workspace.cwd / run_name

            if run_drc.exists():
                op_queue.add(action=lambda: None,
                             description=click.style('Not creating directory',
                                                     fg='red',
                                                     bold=True),
                             extra_description=f'Directory {run_drc} exists')
                targets_exist = True

# do one final check if we will not overwrite existing files
    if targets_exist and not force:
        op_queue.add(action=lambda: None,
                     description=click.style('Not creating runs',
                                             fg='red',
                                             bold=True),
                     extra_description='some targets already exist, '
                     'use --force to override')
        return


# end safety checks

    for i, combination in enumerate(combinations):
        run_name = f'{RUN_PREFIX}{i:04d}'
        run_drc = workspace.cwd / run_name

        op_queue.add(action=run_drc.mkdir,
                     kwargs={
                         'parents': True,
                         'exist_ok': force
                     },
                     description='Creating run',
                     extra_description=f'{run_drc}')

        target_in = ImasHandle(db=options.data.imasdb,
                               shot=source.shot,
                               run=options.data.run_in_start_at + i)
        target_out = ImasHandle(db=options.data.imasdb,
                                shot=source.shot,
                                run=options.data.run_out_start_at + i)

        source.copy_data_to(target_in)

        system.copy_from_template(template_drc, run_drc)

        apply_combination(target_in, run_drc, combination)

        system.write_batchfile(workspace, run_name, template_drc)

        system.update_imas_locations(run=run_drc,
                                     inp=target_in,
                                     out=target_out)

        runs.append({
            'dirname': run_name,
            'data_in': target_in,
            'data_out': target_out,
            'operations': combination
        })

    write_runs_file(runs, workspace)
    write_runs_csv(runs)
