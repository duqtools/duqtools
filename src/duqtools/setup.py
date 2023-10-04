from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Optional

import yaml
from jinja2 import Environment, FileSystemLoader
from pydantic_yaml import parse_yaml_raw_as

from duqtools.api import ImasHandle
from duqtools.config import var_lookup

from .config import Config
from .ids._imas import imasdef
from .operations import op_queue
from .utils import no_op

if TYPE_CHECKING:
    import jinja2

    from duqtools.api import IDSMapping
    from duqtools.systems.jetto import IDS2JettoVariableModel

logger = logging.getLogger(__name__)


class SetupError(Exception):
    ...


def get_template(filename: str) -> jinja2.Template:
    """Load filename as a jinja2 template."""
    path = Path(filename)
    drc = Path(path).parent
    file_loader = FileSystemLoader(str(drc))
    environment = Environment(loader=file_loader, autoescape=True)
    return environment.get_template(path.name)


def _get_key(filename: str, *, key: str):
    """Grab key from unrendered config file."""
    with open(filename, 'rb') as f:
        for line in f:
            try:
                item = yaml.safe_load(line)
                return item[key]
            except (yaml.YAMLError, TypeError, KeyError):
                continue


def _generate_run_dir(drc: Path, cfg: str, force: bool):
    drc.mkdir(exist_ok=force, parents=True)

    with open(drc / 'duqtools.yaml', 'w') as f:
        f.write(cfg)


class ExtrasV210921:
    """Track run number to avoid overwriting existing data in sequential
    runs."""
    MAX_RUN = 9999

    def __init__(self, template_file: str):
        self.n_samples = self._get_n_samples(template_file)
        self.run_numbers: dict[tuple[str, int],
                               int] = defaultdict(lambda: 1000)

    @staticmethod
    def _get_n_samples(template_file: str) -> int:
        """Grab number of samples generated by this config, from
        `create.sampler.n_samples`."""
        n_samples = _get_key(template_file, key='n_samples')

        if not n_samples:
            raise ValueError('`create.sampler.n_samples` must be defined for '
                             'jintrac `v210921` config')

        return n_samples

    def add_system_attrs(self, *, handle: ImasHandle, run: SimpleNamespace):
        """Add system specific attributes to run namespace."""
        data_in_start = self.run_numbers[handle.db, handle.shot]
        data_out_start = data_in_start + self.n_samples

        self.run_numbers[handle.db,
                         handle.shot] = data_out_start + self.n_samples

        if self.run_numbers[handle.db, handle.shot] > self.MAX_RUN:
            raise ValueError(
                f'Cannot write data with run number > {self.MAX_RUN}')

        run.data_in_start = data_in_start
        run.data_out_start = data_out_start


class Variables:
    lookup = var_lookup.filter_type('IDS2jetto-variable')

    def __init__(self, *, handle: ImasHandle):
        self.handle = handle
        self._ids_cache: dict[str, IDSMapping] = {}

    def _get_ids(self, ids: str):
        """Cache ids lookups to avoid repeated data reads."""
        if ids in self._ids_cache:
            mapping = self._ids_cache[ids]
        else:
            mapping = self.handle.get(ids)
            self._ids_cache[ids] = mapping

        return mapping

    @staticmethod
    def is_empty(value: Any) -> bool:
        """Check against imasdef if variable is empty."""
        if isinstance(value, float):
            return value in (imasdef.EMPTY_FLOAT, imasdef.EMPTY_DOUBLE)
        elif isinstance(value, int):
            return value == imasdef.EMPTY_INT
        elif isinstance(value, complex):
            return value == imasdef.EMPTY_COMPLEX

        return False

    def __getattr__(self, key: str):
        try:
            spec: IDS2JettoVariableModel = self.lookup[
                f'ids-{key}']  # type: ignore
        except KeyError as exc:
            msg = f'Cannot find {key!r} in your variable listing (i.e. `variables.yaml`).'
            raise AttributeError(msg) from exc

        value = spec.default

        for item in spec.paths:
            mapping = self._get_ids(item.ids)
            try:
                trial = mapping[item.path]
            except KeyError:
                continue

            if not self.is_empty(trial):
                value = trial
                break

        if value is None:
            raise AttributeError(
                f'No value matches specifications given by: {spec}')

        return value


def substitute_templates(
    *,
    handles: dict[str, ImasHandle],
    template_file: str,
    force: bool,
    base: bool = False,
    output: Optional[str] = None,
):
    """Handle template substitution.

    Parameters
    ----------
    handles : dict[str, ImasHandle]
        Dictionary with Imas handles
    template_file : str
        Path to template file.
    force : bool
        Overwrite files if set to true.
    output : str
        Output subdirectory.
    """
    cwd = Path.cwd()

    template = get_template(template_file)

    if _get_key(template_file, key='system') == 'jetto-v210921':
        add_system_attrs = ExtrasV210921(template_file).add_system_attrs
    else:
        add_system_attrs = no_op  # default to no-op

    for name, handle in handles.items():
        run = SimpleNamespace(name=name, output=output)

        add_system_attrs(run=run, handle=handle)

        variables = Variables(handle=handle)

        cfg = template.render(run=run, variables=variables, handle=handle)

        parse_yaml_raw_as(Config, cfg)  # make sure config is valid

        if output:
            out_drc = cwd / output / name
        else:
            out_drc = cwd / name

        if out_drc.exists() and not force:
            op_queue.add_no_op(
                description='Directory exists',
                extra_description=f'{name} ({out_drc.relative_to(cwd)})')
            op_queue.warning(description='Warning',
                             extra_description='Some targets already exist, '
                             'use --force to override')
        else:
            op_queue.add(
                action=_generate_run_dir,
                kwargs={
                    'drc': out_drc,
                    'cfg': cfg,
                    'force': force
                },
                description='Setup run',
                extra_description=f'{name} ({out_drc.relative_to(cwd)})',
            )


def setup(*, handle, template_file, run_name, force, **kwargs):
    """Setup large scale validation runs for template.

    Parameters
    ----------
    handle : str
        This is the handle to replace into the template.
    template_file : Path
        Path to the template file (jinja2 format).
    run_name : str
        Name of the output directory and run name.
    force : bool
        Set to true to overwrite previous files.
    """
    handles = {run_name: ImasHandle.from_string(handle)}

    substitute_templates(handles=handles,
                         template_file=template_file,
                         force=force)
