from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

from .models import Job, Locations
from .operations import add_to_op_queue, op_queue

if TYPE_CHECKING:
    from .config import Config


@add_to_op_queue('Getting data', 'job {job.path.name} from prominence')
def get_data_from_prominence(job: Job):
    with open(job.lockfile) as f:
        prom_id = f.readline().split()[-1]
        subprocess.run(['prominence', 'download', prom_id])
        archive = job.path.name + '.tgz'
        subprocess.run(['tar', '-xzf', archive, '-C', job.path.parent])
        os.remove(archive)


def sync_prominence(*, cfg: Config, force: bool = False, **kwargs):
    """This function can be used when working with prominence runs to get the
    data from prominence, the prominence client needs to be logged in for this
    to work.

    Parameters
    ----------
    cfg : Config
        The relevant duqtools configuration
    force : bool
        Get data again if a status file exists
    """

    locations = Locations(cfg=cfg)
    jobs = [Job(run.dirname, cfg=cfg) for run in locations.runs]
    for job in jobs:
        if job.has_status and not force:
            op_queue.add_no_op(description='Not getting data',
                               extra_description=job.path.name +
                               ' status file exists')
        elif job.lockfile:
            get_data_from_prominence(job)
        else:
            op_queue.add_no_op(
                description='Not getting data',
                extra_description=job.path.name +
                ' has no lockfile to get the prom id from (is it submitted?)')
