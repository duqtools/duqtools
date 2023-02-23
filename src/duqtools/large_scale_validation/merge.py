import logging
from pathlib import Path

from duqtools.api import ImasHandle

from ..config import cfg, var_lookup
from ..merge import _merge
from ..operations import op_queue
from ..utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)


def merge(**kwargs):
    cwd = Path.cwd()

    variables = tuple(var_lookup.filter_type('IDS-variable').values())
    op_queue.info(description='Merging all known variables')

    config_files = cwd.glob('**/duqtools.yaml')

    for config_file in config_files:
        cfg.parse_file(config_file)

        data_csv = config_file.parent / 'data.csv'
        handles = list(read_imas_handles_from_file(data_csv).values())

        run_name = config_file.parent.name

        handles = [handle for handle in handles if handle.exists()]
        if not handles:
            op_queue.warning(run_name, 'No data to merge.')
            continue

        op_queue.info(run_name, description=f'Merging {len(handles)} datasets')

        template_data = ImasHandle.parse_obj(cfg.create.template_data)

        target_data = template_data.copy()
        target_data.user = str(cfg.create.runs_dir / 'imasdb')

        _merge(
            variables=variables,
            handles=handles,
            target=target_data,
            template=template_data,
            force=False,
        )
