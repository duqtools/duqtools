from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Sequence

from ..config import Config
from ..schema import BaseModel, ImasBaseModel

if TYPE_CHECKING:
    from pathlib import Path

    from ..ids import ImasHandle
    from ._job import Job

logger = logging.getLogger(__name__)


class AbstractSystem(ABC, BaseModel):

    cfg: Config

    @abstractmethod
    def get_runs_dir(self, ) -> Path:
        """Get the directory where the runs should be stored.

        Parameters
        ----------

        Returns
        -------
        Path
        """
        pass

    @abstractmethod
    def write_batchfile(self, run_dir: Path):
        """Write the batchfile used to submit the job inside run directory
        `run_dir`.

        Parameters
        ----------
        run_dir : Path
            directory of run
        """
        pass

    @abstractmethod
    def submit_job(self, job: Job):
        """Submit the job specified by `job` to the system.

        Parameters
        ----------
        job : Job
            job
        """
        pass

    @abstractmethod
    def copy_from_template(self, source_drc: Path, target_drc: Path):
        """Copy from template directory `source_drc` to target directory
        `target_drc`

        Parameters
        ----------
        source_drc : Path
            source directory
        target_drc : Path
            target directory
        """
        pass

    @abstractmethod
    def imas_from_path(self, template_drc: Path) -> ImasHandle:
        """It takes a path, and finds out the IMAS entry associated with it.

        Parameters
        ----------
        template_drc : Path
            folder from which to extract IMAS location

        Returns
        -------
        ImasHandle
        """
        pass

    @abstractmethod
    def update_imas_locations(
        self,
        run: Path,
        inp: ImasBaseModel,
        out: ImasBaseModel,
        **kwargs,
    ):
        """Set the imas entries for the run, both input imas file `in` and
        output imas file `out`.

        Parameters
        ----------
        run : Path
            run directory
        inp : ImasBaseModel
            Imas entry to use as input
        out : ImasBaseModel
            Imas entry to use as output
        """
        pass

    @abstractmethod
    def get_data_in_handle(
        self,
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ) -> ImasHandle:
        """Get handle for data input. This method is used to copy the template
        data to wherever the system expects the input data to be.

        Parameters
        ----------
        dirname : Path
            run directory
        source : ImasHandle
            template Imas data
        seq_number : int
            sequential number, used by some systems
        options :
            create.data key from the config
        """
        pass

    @abstractmethod
    def get_data_out_handle(
        self,
        *,
        dirname: Path,
        source: ImasHandle,
        seq_number: int,
        options,
    ) -> ImasHandle:
        """Get handle for data output. This method is used to set the locations
        in the system correct (later on), in a sense this method is
        superfluous.

        Parameters
        ----------
        dirname : Path
            run directory
        source : ImasHandle
            template Imas data
        seq_number : int
            sequential number, used by some systems
        options :
            create.data key from the config
        """
        pass

    @abstractmethod
    def submit_array(
        self,
        jobs: Sequence[Job],
        *,
        max_jobs: int = 10,
        max_array_size: int = 100,
        **kwargs,
    ):
        """submit_array method used for submitting the jobs in an array
        fashion, its perfectly fine to just throw an error if the system does
        not support it.

        Parameters
        ----------
        jobs : Sequence[Job]
            jobs
        max_jobs : int
            max_jobs
        max_array_size : int
            max_array_size
        kwargs :
            optional arguments
        """
        pass
