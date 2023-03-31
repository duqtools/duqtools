import logging
import shutil
import warnings
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from .apply_model import apply_model
from .cleanup import remove_run
from .config import Config, cfg
from .ids import ImasHandle
from .matrix_samplers import get_matrix_sampler
from .models import Locations, Run, Runs
from .operations import add_to_op_queue, op_queue
from .system import get_system

logger = logging.getLogger(__name__)

RUN_PREFIX = 'run_'


class CreateError(Exception):
    ...


class CreateManager:
    """Docstring for CreateManager."""

    def __init__(self):
        self.options = cfg.create

        if not self.options:
            logger.warning('No create options specified.')
            raise CreateError('No create options specified in config.')

        self.template_drc = self.options.template
        self.system = get_system()
        self.runs_dir = self.system.get_runs_dir()
        self.source = self._get_source_handle()

        locations = Locations()
        self.runs_yaml = locations.runs_yaml
        self.data_csv = locations.data_csv

    def _get_source_handle(self) -> ImasHandle:
        if not self.options.template_data:
            source = self.system.imas_from_path(self.template_drc)
        else:
            source = ImasHandle.parse_obj(self.options.template_data)

        logger.info('Source data: %s', source)

        return source

    def generate_ops_list(self) -> list[Any]:
        """Generate set of operations for a run."""
        dimensions = self.options.dimensions
        matrix_sampler = get_matrix_sampler(self.options.sampler.method)
        matrix = tuple(model.expand() for model in dimensions)
        ops_list = matrix_sampler(*matrix, **dict(self.options.sampler))

        return ops_list

    def make_run_models(self, ops_list: Sequence[Any],
                        absolute_dirpath: bool) -> list[Run]:
        """Take list of operations and create run models."""
        run_models = []

        for i, operations in enumerate(ops_list):
            dirname = self.runs_dir / f'{RUN_PREFIX}{i:04d}'

            data_in = self.system.get_data_in_handle(
                dirname=dirname,
                seq_number=i,
                source=self.source,
                options=self.options.data,
            )

            data_out = self.system.get_data_out_handle(
                dirname=dirname,
                seq_number=i,
                source=self.source,
                options=self.options.data,
            )

            model = Run(dirname=dirname,
                        shortname=dirname.name,
                        data_in=data_in,
                        data_out=data_out,
                        operations=operations)

            run_models.append(model)

        return run_models

    def runs_yaml_exists(self) -> bool:
        """Check if runs.yaml exists."""
        if self.runs_yaml.exists():
            op_queue.add_no_op(description='Not creating runs.yaml',
                               extra_description=f'{self.runs_yaml} exists')
            return True
        return False

    def data_locations_exist(self, models: Sequence[Run]) -> bool:
        """Check IDS coordinates and raise if any exist."""
        any_exists = False

        for model in models:
            if ImasHandle.parse_obj(model.data_in).exists():
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
            if model.dirname.exists():
                op_queue.add_no_op(
                    description='Not creating directory',
                    extra_description=f'Directory {model.dirname} exists',
                )

                any_exists = True

        return any_exists

    def warn_no_create_runs(self):
        """Add warning to op queue if runs will not be created."""
        op_queue.warning(description='Warning',
                         extra_description='Some targets already exist, '
                         'use --force to override')

    @add_to_op_queue('Setting inital condition of', '{data_in}', quiet=True)
    def apply_operations(self, data_in: ImasHandle, run_dir: Path,
                         operations: list[Any]):
        for model in operations:
            apply_model(model, run_dir=run_dir, ids_mapping=data_in)

    @add_to_op_queue('Writing runs', '{self.runs_yaml}', quiet=True)
    def write_runs_file(self, runs: Sequence[Run]) -> None:
        runs = Runs.parse_obj(runs)

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with open(self.runs_yaml, 'w') as f:
                runs.yaml(stream=f)

            # Only if it is a different directory
            if self._is_runs_dir_different_from_config_dir():
                with open(self.runs_dir / 'runs.yaml', 'w') as f:
                    runs.yaml(stream=f)

    @add_to_op_queue('Writing csv', quiet=True)
    def write_runs_csv(self, runs: Sequence[Run], cfg: Config):
        fname = self.data_csv

        prefix = f'{cfg.tag}.' if cfg.tag else ''

        run_map = {
            f'{prefix}{run.shortname}': run.data_out.dict()
            for run in runs
        }
        df = pd.DataFrame.from_dict(run_map, orient='index')
        df.to_csv(fname)

        if self._is_runs_dir_different_from_config_dir():
            df.to_csv(self.runs_dir / fname)

    @add_to_op_queue('Storing duqtools.yaml inside runs_dir', quiet=True)
    def copy_config(self, config):
        if self._is_runs_dir_different_from_config_dir():
            shutil.copyfile(Path.cwd() / config,
                            self.runs_dir / 'duqtools.yaml')

    def _is_runs_dir_different_from_config_dir(self) -> bool:
        """Return True if the runs dir is different from the duqtools config
        dir."""
        return Path.cwd().resolve() != self.runs_dir.resolve()

    def create_run(self, model: Run, *, force: bool = False):
        """Take a run model and create it."""
        op_queue.add(action=model.dirname.mkdir,
                     kwargs={
                         'parents': True,
                         'exist_ok': force
                     },
                     description='Creating run',
                     extra_description=f'{model.dirname}')

        self.source.copy_data_to(model.data_in)

        self.system.copy_from_template(self.template_drc, model.dirname)

        self.apply_operations(model.data_in, model.dirname, model.operations)

        self.system.write_batchfile(model.dirname, cfg)

        self.system.update_imas_locations(run=model.dirname,
                                          inp=model.data_in,
                                          out=model.data_out)


def create(*, force, config, absolute_dirpath: bool = False, **kwargs):
    """Create input for jetto and IDS data structures.

    Parameters
    ----------
    force : bool
        Override protection if data and directories already exist.
    config : Path
        Config file location

    **kwargs
        Unused.
    """
    create_mgr = CreateManager()

    ops_list = create_mgr.generate_ops_list()

    runs = create_mgr.make_run_models(ops_list, absolute_dirpath)

    if not force:

        target_exists = any([
            create_mgr.runs_yaml_exists(),
            create_mgr.data_locations_exist(runs),
            create_mgr.run_dirs_exist(runs),
        ])

        if target_exists:
            create_mgr.warn_no_create_runs()
            return

    for model in runs:
        create_mgr.create_run(model, force=force)

    create_mgr.write_runs_file(runs)
    create_mgr.write_runs_csv(runs, cfg)
    create_mgr.copy_config(config)


def recreate(*, runs: Sequence[Path], **kwargs):
    """Create input for jetto and IDS data structures.

    Parameters
    ----------
    runs : Sequence[Path]
        Run names to recreate.
    **kwargs
        Unused.
    """
    create_mgr = CreateManager()

    run_dict = {run.shortname: run for run in Locations().runs}

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
        create_mgr.create_run(model)
