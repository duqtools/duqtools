from __future__ import annotations

import logging
import shutil
import warnings
from pathlib import Path
from typing import Any, Sequence

import pandas as pd
from pydantic_yaml import to_yaml_file

from .apply_model import apply_model
from .cleanup import remove_run
from .config import Config
from .ids import ImasHandle
from .matrix_samplers import get_matrix_sampler
from .models import Job, Locations, Run, Runs
from .operations import add_to_op_queue, op_queue
from .systems import get_system

logger = logging.getLogger(__name__)

RUN_PREFIX = 'run_'


class CreateError(Exception):
    ...


class CreateManager:
    """Docstring for CreateManager."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        if not self.cfg.create:
            logger.warning('No create options specified.')
            raise CreateError('No create options specified in config.')

        self.options = self.cfg.create

        self.template_drc = self.options.template
        self.system = get_system(cfg=cfg)
        self.runs_dir = self.system.get_runs_dir()
        self.source = self._get_source_handle()

        locations = Locations(cfg=cfg)
        self.runs_yaml = locations.runs_yaml
        self.data_csv = locations.data_csv

    def _get_source_handle(self) -> ImasHandle:
        template_data = self.options.template_data

        if not template_data:
            if not self.template_drc:
                raise ValueError('Missing `create.template`')
            source = self.system.imas_from_path(self.template_drc)
        else:
            source = ImasHandle.model_validate(template_data,
                                               from_attributes=True)

        logger.info('Source data: %s', source)

        return source

    def get_base_ops(self) -> list[Any]:
        """Generate base operations that are always applied."""
        base_ops = [op.convert() for op in self.options.operations]
        return base_ops

    def generate_ops_dict(self,
                          *,
                          base_only: bool = False) -> dict[str, list[Any]]:
        """Generate set of operations for a run."""
        base_ops = self.get_base_ops()

        if base_only:
            return {'base': base_ops}

        matrix = tuple(model.expand() for model in self.options.dimensions)
        matrix_sampler = get_matrix_sampler(self.options.sampler.method)

        sampled_ops_lists = matrix_sampler(*matrix,
                                           **dict(self.options.sampler))

        ops_dict = {}
        for i, ops_list in enumerate(sampled_ops_lists):
            name = f'{RUN_PREFIX}{i:04d}'
            ops_dict[name] = [*base_ops, *ops_list]

        return ops_dict

    def make_run_models(self, *, ops_dict: dict[str, list[Any]],
                        absolute_dirpath: bool) -> list[Run]:
        """Take list of operations and create run models."""
        run_models = []

        for name, operations in ops_dict.items():
            dirname = self.runs_dir / name

            data_in = self.system.get_data_in_handle(
                dirname=dirname,
                source=self.source,
            )

            data_out = self.system.get_data_out_handle(
                dirname=dirname,
                source=self.source,
            )

            model = Run(dirname=dirname,
                        shortname=name,
                        data_in=data_in,
                        data_out=data_out)
            model.operations = operations  # it bugs out so don't validate

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
            if ImasHandle.model_validate(model.data_in,
                                         from_attributes=True).exists():
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
            apply_model(model,
                        run_dir=run_dir,
                        ids_mapping=data_in,
                        system=self.system)

    @add_to_op_queue('Writing runs', '{self.runs_yaml}', quiet=True)
    def write_runs_file(self, runs: Sequence[Run]) -> None:
        runs = Runs.model_validate(runs, from_attributes=True)

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            to_yaml_file(self.runs_yaml, runs)

            # Only if it is a different directory
            if self._is_runs_dir_different_from_config_dir():
                to_yaml_file(self.runs_dir / 'runs.yaml', runs)

    @add_to_op_queue('Writing csv', quiet=True)
    def write_runs_csv(self, runs: Sequence[Run]):
        fname = self.data_csv

        prefix = f'{self.cfg.tag}.' if self.cfg.tag else ''

        run_map = {
            f'{prefix}{run.shortname}': run.data_out.model_dump()
            for run in runs if run.data_out
        }
        df = pd.DataFrame.from_dict(run_map, orient='index')
        df.to_csv(fname)

        if self._is_runs_dir_different_from_config_dir():
            df.to_csv(self.runs_dir / fname)

    def copy_config(self):
        if self.cfg._path is None:
            return

        if self._is_runs_dir_different_from_config_dir():
            op_queue.add(
                action=shutil.copyfile,
                args=(
                    Path.cwd() / self.cfg._path,
                    self.runs_dir / 'duqtools.yaml',
                ),
                description='Copying config to run directory',
                quiet=True,
            )

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

        self.source.copy_data_to(
            ImasHandle.model_validate(model.data_in, from_attributes=True))

        if self.template_drc:
            self.system.copy_from_template(self.template_drc, model.dirname)

        self.apply_operations(model.data_in, model.dirname, model.operations)

        self.system.write_batchfile(model.dirname)

        if model.data_in and model.data_out:
            self.system.update_imas_locations(run=model.dirname,
                                              inp=model.data_in,
                                              out=model.data_out,
                                              template_drc=self.template_drc)
        else:
            raise Exception(
                'data not present in model, this should not happen')


def create(*,
           cfg: Config,
           force: bool = False,
           no_sampling: bool = False,
           absolute_dirpath: bool = False,
           **kwargs) -> list[Run]:
    """Create input for jetto and IDS data structures.

    Parameters
    ----------
    force : bool
        Override protection if data and directories already exist.
    cfg : Config
        Duqtools config
    no_sampling : bool
        If true, create base run by ignoring `sampler`/`dimensions`.

    **kwargs
        Unused.
    """
    create_mgr = CreateManager(cfg)

    ops_dict = create_mgr.generate_ops_dict(base_only=no_sampling)

    runs = create_mgr.make_run_models(
        ops_dict=ops_dict,
        absolute_dirpath=absolute_dirpath,
    )

    if not force:

        target_exists = any([
            create_mgr.runs_yaml_exists(),
            create_mgr.data_locations_exist(runs),
            create_mgr.run_dirs_exist(runs),
        ])

        if target_exists:
            create_mgr.warn_no_create_runs()
            return []

    for model in runs:
        create_mgr.create_run(model, force=force)

    create_mgr.write_runs_file(runs)
    create_mgr.write_runs_csv(runs)
    create_mgr.copy_config()

    return runs


def create_api(config: dict, **kwargs) -> dict[str, tuple[Job, Run]]:
    """Wrapper around create for python api."""
    cfg = Config.from_dict(config)
    runs = create(cfg=cfg, **kwargs)

    if len(runs) == 0:
        raise CreateError('No runs were created, check logs for errors.')

    return {
        str(run.shortname): (Job(run.dirname, cfg=cfg), run)
        for run in runs
    }


def recreate(*, cfg: Config, runs: Sequence[Path], **kwargs):
    """Create input for jetto and IDS data structures.

    Parameters
    ----------
    cfg : Config
        Duqtools config.
    runs : Sequence[Path]
        Run names to recreate.
    **kwargs
        Unused.
    """
    create_mgr = CreateManager(cfg)

    run_dict = {run.shortname: run for run in Locations(cfg=cfg).runs}

    run_models = []
    for run in runs:
        if run not in run_dict:
            raise ValueError(f'`{run}` not in `runs.yaml`.')

        model = run_dict[run]
        model.data_in = ImasHandle.model_validate(model.data_in,
                                                  from_attributes=True)
        assert model.data_in

        model.data_out = ImasHandle.model_validate(model.data_out,
                                                   from_attributes=True)
        assert model.data_out

        model.data_in.delete()
        remove_run(model)

        run_models.append(model)

    for model in run_models:
        create_mgr.create_run(model)

    return run_models


def recreate_api(config: dict, runs: Sequence[Path],
                 **kwargs) -> dict[str, tuple[Job, Run]]:
    """Wrapper around create for python api."""
    cfg = Config.from_dict(config)
    runs = recreate(cfg=cfg, runs=runs, **kwargs)

    if len(runs) == 0:
        raise CreateError('No runs were recreated, check logs for errors.')

    return {
        str(run.shortname): (Job(run.dirname, cfg=cfg), run)
        for run in runs
    }
