import logging
from pathlib import Path
from typing import List, Sequence

import pandas as pd

from .apply_model import apply_model
from .cleanup import remove_run
from .config import cfg
from .ids import ImasHandle
from .matrix_samplers import get_matrix_sampler
from .models import WorkDirectory
from .operations import add_to_op_queue, op_queue
from .schema.runs import Run, Runs
from .system import get_system

logger = logging.getLogger(__name__)

RUN_PREFIX = 'run_'


class CreateError(Exception):
    ...


class RunCreator:
    """Docstring for RunCreator."""

    def __init__(self):
        self.options = cfg.create

        if not self.options:
            logger.warning('No create options specified.')
            raise CreateError('No create options specified in config.')

        self.template_drc = self.options.template
        self.workspace = WorkDirectory.parse_obj(cfg.workspace)
        self.system = get_system()
        self.source = self._get_source_handle()

    def _get_source_handle(self) -> ImasHandle:
        if not self.options.template_data:
            source = self.system.imas_from_path(self.template_drc)
        else:
            source = ImasHandle.parse_obj(self.options.template_data)

        logger.info('Source data: %s', source)

        return source

    def generate_combinations(self):
        dimensions = self.options.dimensions
        matrix_sampler = get_matrix_sampler(self.options.sampler.method)
        matrix = tuple(model.expand() for model in dimensions)
        combinations = matrix_sampler(*matrix, **dict(self.options.sampler))

        return combinations

    def combinations2runs(self, combinations) -> List[Run]:
        runs = []

        for i, operations in enumerate(combinations):
            dirname = f'{RUN_PREFIX}{i:04d}'

            data_in = ImasHandle(db=self.options.data.imasdb,
                                 shot=self.source.shot,
                                 run=self.options.data.run_in_start_at + i)
            data_out = ImasHandle(db=self.options.data.imasdb,
                                  shot=self.source.shot,
                                  run=self.options.data.run_out_start_at + i)

            model = Run(dirname=dirname,
                        data_in=data_in,
                        data_out=data_out,
                        operations=operations)
            runs.append(model)

        return runs

    def runs_yaml_exists(self) -> bool:
        """Check if runs.yaml exists."""
        if self.workspace.runs_yaml.exists():
            op_queue.add_no_op(
                description='Not creating runs.yaml',
                extra_description=f'{self.workspace.runs_yaml} exists')
            return True
        return False

    def data_locations_exist(self, models: Sequence[Run]) -> bool:
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

    def run_dirs_exist(self, models: Sequence[Run]) -> bool:
        """Check if any of the run dirs exist."""
        any_exists = False

        for model in models:
            run_drc = self.workspace.cwd / model.dirname

            if run_drc.exists():
                op_queue.add_no_op(
                    description='Not creating directory',
                    extra_description=f'Directory {run_drc} exists',
                )

            any_exists = True

        return any_exists

    def warn_no_create_runs(self):
        """Add warning to op queue if runs will not be created."""
        op_queue.add_no_op(description='Not creating runs',
                           extra_description='some targets already exist, '
                           'use --force to override')

    @add_to_op_queue('Setting inital condition of', '{data_in}', quiet=True)
    def apply_combination(self, data_in: ImasHandle, run_dir: Path,
                          combination):
        for model in combination:
            apply_model(model, run_dir=run_dir, ids_mapping=data_in)

    @add_to_op_queue('Writing runs', '{workspace.runs_yaml}', quiet=True)
    def write_runs_file(self, runs: Sequence[Run]) -> None:
        runs = Runs.parse_obj(runs)
        with open(self.workspace.runs_yaml, 'w') as f:
            runs.yaml(stream=f)

    @add_to_op_queue('Writing csv', quiet=True)
    def write_runs_csv(self, runs, fname: str = 'data.csv'):
        run_map = {run['dirname']: run['data_out'].dict() for run in runs}
        df = pd.DataFrame.from_dict(run_map, orient='index')
        df.to_csv(fname)

    def create_run(self, model: Run, *, force: bool = False):
        """Take a run model and create it."""
        run_drc = self.workspace.cwd / model.dirname

        op_queue.add(action=run_drc.mkdir,
                     kwargs={
                         'parents': True,
                         'exist_ok': force
                     },
                     description='Creating run',
                     extra_description=f'{run_drc}')

        self.source.copy_data_to(model.data_in)

        self.system.copy_from_template(self.template_drc, run_drc)

        self.apply_combination(model.data_in, run_drc, model.operations)

        self.system.write_batchfile(self.workspace, model.dirname,
                                    self.template_drc)

        self.system.update_imas_locations(run=run_drc,
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
    run_creator = RunCreator()

    combinations = run_creator.generate_combinations()

    runs = run_creator.combinations2runs(combinations)

    if not force:

        target_exists = any([
            run_creator.runs_yaml_exists(),
            run_creator.data_locations_exist(runs),
            run_creator.run_dirs_exist(runs),
        ])

        if target_exists:
            run_creator.warn_no_create_runs()
            return

    run_creator.write_runs_file(runs)
    run_creator.write_runs_csv(runs)

    for model in runs:
        run_creator.create_run(model, force=force)


def recreate(*, runs, **kwargs):
    run_creator = RunCreator()

    run_dict = {str(run.dirname): run for run in run_creator.workspace.runs}

    run_models = []
    for run in runs:
        if run not in run_dict:
            raise ValueError(f'`{run}` not in `runs.yaml`.')

        model = run_dict[run]
        model.data_in = ImasHandle.parse_obj(model.data_in)
        model.data_out = ImasHandle.parse_obj(model.data_out)

        model.data_in.delete()
        remove_run(model)

        run_models.append(model)

    for model in run_models:
        run_creator.create_run(model)
