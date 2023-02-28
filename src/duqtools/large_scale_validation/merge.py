import logging
from pathlib import Path
from typing import Sequence

import pandas as pd

from duqtools.api import ImasHandle

from ..config import cfg
from ..merge import _merge, _resolve_variables
from ..models import Job, Locations
from ..operations import add_to_op_queue, op_queue

logger = logging.getLogger(__name__)


@add_to_op_queue('Writing csv', '{fname}')
def _write_data_csv(handles: dict[str, ImasHandle], fname: str = 'data.csv'):
    """Write handles to a data.csv file."""
    df = pd.DataFrame.from_dict(handles, orient='index')
    df.to_csv(fname)


def merge(force: bool, var_names: Sequence[str], **kwargs):
    cwd = Path.cwd()

    variables = _resolve_variables(var_names)

    config_files = cwd.glob('**/duqtools.yaml')

    target_handles = {}

    for config_file in config_files:
        run_name = config_file.parent.name

        cfg.parse_file(config_file)

        config_dir = config_file.parent

        runs = Locations(config_dir).runs
        runs = (run for run in runs if Job(run.dirname).is_completed)
        handles = (ImasHandle.parse_obj(run.data_out) for run in runs)
        handles = [handle for handle in handles if handle.exists()]

        if not handles:
            op_queue.warning(run_name, 'No data to merge.')
            continue

        op_queue.info(run_name,
                      extra_description=f'Merging {len(handles)} datasets')

        template_data = handles[0]

        target_data = template_data.copy()
        target_data.user = str(cfg.create.runs_dir / 'imasdb')
        target_handles[f'{run_name}_merged'] = target_data.dict()

        _merge(
            variables=variables,
            handles=handles,
            target=target_data,
            template=template_data,
            force=force,
        )

    _write_data_csv(target_handles, fname='merge_data.csv')
