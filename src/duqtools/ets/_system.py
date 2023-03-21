import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from ..config import Config, cfg
from ..ids import ImasHandle
from ..models import AbstractSystem, Job, Locations
from ..operations import add_to_op_queue

if sys.version_info < (3, 10):
    pass
else:
    pass

logger = logging.getLogger(__name__)


class Ets6System(AbstractSystem):
    """System that can be used to create runs for ets."""

    @staticmethod
    def get_runs_dir() -> Path:
        raise NotImplementedError('get_runs_dir')
        path = Locations().jruns_path
        runs_dir = cfg.create.runs_dir  # type: ignore
        if not runs_dir:
            abs_cwd = str(Path.cwd().resolve())
            abs_jruns = str(path.resolve())
            # Check if jruns is parent dir of current dir
            if abs_cwd.startswith(abs_jruns):
                runs_dir = Path()
            else:  # jruns is somewhere else
                count = 0
                while True:  # find the next free folder
                    runs_dir = f'duqtools_experiment_{count:04d}'
                    if not (path / runs_dir).exists():
                        break
                    count = count + 1
        return path / runs_dir

    @staticmethod
    @add_to_op_queue('Writing new batchfile', '{run_dir.name}', quiet=True)
    def write_batchfile(run_dir: Path, cfg: Config):
        raise NotImplementedError('writE_batchfile not implemented')

    @staticmethod
    def submit_job(job: Job):
        # Make sure we get a new correct status
        raise NotImplementedError('submission not implemented')

    @staticmethod
    def submit_array(jobs: Sequence[Job], max_jobs: int):
        raise NotImplementedError('array submission not implemented')

    @staticmethod
    @add_to_op_queue('Copying template to', '{target_drc}', quiet=True)
    def copy_from_template(source_drc: Path, target_drc: Path):
        raise NotImplementedError('copy_from_template')

    @staticmethod
    def imas_from_path(template_drc: Path) -> ImasHandle:
        raise NotImplementedError('imas_from_path')


#        return ImasHandle(
#            db  =,  # type: ignore
#            user=,  # type: ignore
#            run =,  # type: ignore
#            shot=)  # type: ignore

    @staticmethod
    @add_to_op_queue('Updating imas locations of', '{run}', quiet=True)
    def update_imas_locations(run: Path, inp: ImasHandle, out: ImasHandle):
        raise NotImplementedError('update_imas_location')

    @staticmethod
    def get_data_in_handle(
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ):
        """Get handle for data input."""
        return ImasHandle(
            user=options.user,
            db=options.imasdb,
            shot=source.shot,
            run=options.run_in_start_at + seq_number,
        )

    @staticmethod
    def get_data_out_handle(
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ):
        """Get handle for data output."""
        return ImasHandle(
            user=options.user,
            db=options.imasdb,
            shot=source.shot,
            run=options.run_out_start_at + seq_number,
        )
