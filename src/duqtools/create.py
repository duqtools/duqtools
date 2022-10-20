import logging
from pathlib import Path
from typing import Sequence

import pandas as pd

from .apply_model import apply_model
from .config import cfg
from .ids import ImasHandle
from .matrix_samplers import get_matrix_sampler
from .models import WorkDirectory
from .operations import add_to_op_queue, op_queue
from .schema.runs import Run, Runs
from .system import get_system

logger = logging.getLogger(__name__)

RUN_PREFIX = 'run_'


def any_data_locations_exist(models: Sequence[ImasHandle]):
    """Check IDS coordinates and raise if any exist."""
    any_exists = False

    for model in models:
        if model.data_in.exists():
            logger.info('Target %s already exists', model.data_in)
            op_queue.add_no_op(
                description='Not creating IDS',
                extra_description=f'IDS entry {model.data_in} exists')
            any_exists = True

    return any_exists


def any_run_dirs_exist(models: Sequence[Run], *, workspace):
    any_exists = False

    for model in models:
        run_drc = workspace.cwd / model.dirname

        if run_drc.exists():
            op_queue.add_no_op(
                description='Not creating directory',
                extra_description=f'Directory {run_drc} exists',
            )

        any_exists = True

    return any_exists


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


def create_run(model: Run, *, template_drc: Path, source: ImasHandle,
               workspace: WorkDirectory, force: bool):
    """Take a run model and create it."""
    system = get_system()

    run_drc = workspace.cwd / model.dirname

    op_queue.add(action=run_drc.mkdir,
                 kwargs={
                     'parents': True,
                     'exist_ok': force
                 },
                 description='Creating run',
                 extra_description=f'{run_drc}')

    source.copy_data_to(model.data_in)

    system.copy_from_template(template_drc, run_drc)

    apply_combination(model.data_in, run_drc, model.operations)

    system.write_batchfile(workspace, model.dirname, template_drc)

    system.update_imas_locations(run=run_drc,
                                 inp=model.data_in,
                                 out=model.data_out)


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

    runs = []

    # Create run models

    for i, operations in enumerate(combinations):
        dirname = f'{RUN_PREFIX}{i:04d}'

        data_in = ImasHandle(db=options.data.imasdb,
                             shot=source.shot,
                             run=options.data.run_in_start_at + i)
        data_out = ImasHandle(db=options.data.imasdb,
                              shot=source.shot,
                              run=options.data.run_out_start_at + i)

        model = Run(dirname=dirname,
                    data_in=data_in,
                    data_out=data_out,
                    operations=operations)
        runs.append(model)

    # Safety checks

    targets_exist = False

    if not force and workspace.runs_yaml.exists():
        op_queue.add_no_op(description='Not creating runs.yaml',
                           extra_description=f'{workspace.runs_yaml} exists')

        targets_exist = True

    if not force and any_data_locations_exist(runs):
        targets_exist = True

    if not force and any_run_dirs_exist(runs, workspace=workspace):
        targets_exist = True

    if not force and targets_exist:
        op_queue.add_no_op(description='Not creating runs',
                           extra_description='some targets already exist, '
                           'use --force to override')
        return

    # End safety checks

    write_runs_file(runs, workspace)
    write_runs_csv(runs)

    for model in runs:
        create_run(model,
                   source=source,
                   template_drc=template_drc,
                   force=force)


def recreate(*, force, runs, **kwargs):
    options = cfg.create

    template_drc = options.template

    workspace = WorkDirectory.parse_obj(cfg.workspace)

    run_dict = {str(run.dirname): run for run in workspace.runs}

    for run in runs:
        if run not in run_dict:
            raise ValueError(f'`{run}` not in `runs.yaml`.')

    system = get_system()

    if not options.template_data:
        source = system.imas_from_path(template_drc)
    else:
        source = ImasHandle.parse_obj(options.template_data)

    for run in runs:
        model = run_dict[run]

        create_run(model,
                   source=source,
                   template_drc=template_drc,
                   workspace=workspace,
                   force=force)
