import logging
from pathlib import Path

from duqtools.api import ImasHandle

from ..config import cfg, var_lookup
from ..merge import _merge
from ..models import Job, Locations
from ..operations import op_queue

logger = logging.getLogger(__name__)


def merge(force: bool, **kwargs):
    cwd = Path.cwd()

    variables = tuple(var_lookup.filter_type('IDS-variable').values())
    op_queue.info(description='Merging all known variables')

    config_files = cwd.glob('**/duqtools.yaml')

    for config_file in config_files:
        cfg.parse_file(config_file)

        config_dir = config_file.parent

        runs = Locations(config_dir).runs

        handles = []

        for run in runs:
            if not Job(run.dirname).is_completed:
                continue
            handle = ImasHandle.parse_obj(run.data_out)
            if not handle.exists():
                continue

            handles.append(handle)

        run_name = config_file.parent.name

        if not handles:
            op_queue.warning(run_name, 'No data to merge.')
            continue

        op_queue.info(run_name,
                      extra_description=f'Merging {len(handles)} datasets')

        template_data = handles[0]

        target_data = template_data.copy()
        target_data.user = str(cfg.create.runs_dir / 'imasdb')

        _merge(
            variables=variables,
            handles=handles,
            target=target_data,
            template=template_data,
            force=force,
        )
