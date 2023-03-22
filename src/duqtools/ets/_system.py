import logging
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

from ..config import Config
from ..ids import ImasHandle
from ..models import AbstractSystem, Job
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
        return Path()

    @staticmethod
    @add_to_op_queue('Writing new batchfile', '{run_dir.name}', quiet=True)
    def write_batchfile(run_dir: Path, cfg: Config):
        pass

    #raise NotImplementedError('writE_batchfile not implemented')

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
        shutil.copy(source_drc, target_drc)

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
    def update_imas_locations(run: Path, inp: ImasHandle, out: ImasHandle,
                              cfg_filename: Path):
        #raise NotImplementedError('update_imas_location')
        new_input = []
        with open(run / cfg_filename) as f:
            for line in f.readlines():
                if line.startswith('START.output_run'):
                    new_input.append('START.output_run = ' + str(out.run) +
                                     '\n')
                elif line.startswith('START.input_run'):
                    new_input.append('START.input_run = ' + str(inp.run) +
                                     '\n')
                elif line.startswith('START.shot_number'):
                    new_input.append('START.shout_number = ' + str(inp.shot) +
                                     '\n')
                else:
                    new_input.append(line)
        with open(run / cfg_filename, 'w') as f:
            f.write(''.join(new_input))

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
