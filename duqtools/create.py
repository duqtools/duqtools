import logging
from typing import Iterable

from duqtools.config import cfg

from .ids import IDSMapping, ImasHandle
from .ids.dimensions import apply_model
from .matrix_samplers import get_matrix_sampler
from .models import WorkDirectory
from .operations import confirm_operations, op_queue
from .schema.runs import Runs
from .system import get_system

logger = logging.getLogger(__name__)

RUN_PREFIX = 'run_'


def fail_if_locations_exist(locations: Iterable[ImasHandle]):
    """Check IDS coordinates and raise if any exist."""
    any_exists = False
    for location in locations:
        if location.exists():
            logger.info('Target %s already exists', location)
            any_exists = True
    if any_exists:
        raise IOError(
            'Found existing target location(s), use `duqtools clean` to '
            'remove or `--force` to override.')


def apply_combination(target_in: ImasHandle, combination) -> None:
    core_profiles = target_in.get('core_profiles')
    ids_mapping = IDSMapping(core_profiles)

    for model in combination:
        apply_model(model, ids_mapping)

        logger.info('Writing data entry: %s', target_in)
        with target_in.open() as data_entry_target:
            core_profiles.put(db_entry=data_entry_target)


def write_runs_file(runs: list, workspace) -> None:

    runs = Runs.parse_obj(runs)
    with open(workspace.runs_yaml, 'w') as f:
        runs.yaml(stream=f)


@confirm_operations
def create(*, force, dry_run, **kwargs):
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

    source = system.imas_from_path(template_drc)
    logger.info('Source data: %s', source)

    matrix = tuple(dim.expand() for dim in dimensions)
    combinations = matrix_sampler(*matrix, **dict(options.sampler))

    if not force:
        if workspace.runs_yaml.exists():
            raise IOError(
                'Directory is not empty, use `duqtools clean` to clear or '
                '`--force` to override.')

        locations = (ImasHandle(db=options.data.db,
                                shot=source.shot,
                                run=options.data.run_in_start_at + i)
                     for i in range(len(combinations)))

        fail_if_locations_exist(locations)

    runs = []

    for i, combination in enumerate(combinations):
        run_name = f'{RUN_PREFIX}{i:04d}'
        run_drc = workspace.cwd / run_name

        op_queue.add(action=lambda run_drc=run_drc: run_drc.mkdir(
            parents=True, exist_ok=force),
                     description=f'Create folder {run_drc}')

        target_in = ImasHandle(db=options.data.db,
                               shot=source.shot,
                               run=options.data.run_in_start_at + i)
        target_out = ImasHandle(db=options.data.db,
                                shot=source.shot,
                                run=options.data.run_out_start_at + i)

        op_queue.add(action=lambda: source.copy_ids_entry_to(target_in),
                     description=f'Create {target_in} from {source}')

        op_queue.add(
            action=lambda combination=combination, target_in=target_in,
            target_out=target_out: apply_combination(target_in, combination),
            description=f'Applying combination {combination} to {target_in}')

        op_queue.add(
            action=lambda run_drc=run_drc: system.copy_from_template(
                template_drc, run_drc),
            description=f'Copying template from {template_drc} to {run_drc}')

        op_queue.add(action=lambda run_name=run_name: system.write_batchfile(
            workspace, run_name),
                     description=f'Writing new batchfile for {run_name}')

        op_queue.add(action=lambda run_drc=run_drc, target_in=target_in,
                     target_out=target_out: system.update_imas_locations(
                         run=run_drc, inp=target_in, out=target_out),
                     description=f'Updating imas locations of {run_drc} to \n'
                     'in: {target_in}\nout: {target_out}')

        runs.append({
            'dirname': run_name,
            'data_in': target_in,
            'data_out': target_out,
            'operations': combination
        })

    op_queue.add(action=lambda: write_runs_file(runs, workspace),
                 description=f'Writing out {workspace.runs_yaml}')
