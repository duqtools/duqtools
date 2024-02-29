from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from pathlib import Path

    from duqtools.api import ImasHandle, Job
    from duqtools.config import Config
    from duqtools.ids._schema import ImasBaseModel

logger = logging.getLogger(__name__)


class AbstractSystem(ABC):

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.options = cfg.system

    @abstractmethod
    def get_runs_dir(self) -> Path:
        """Get the directory where the runs should be stored.

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
            Directory of run
        """
        pass

    @abstractmethod
    def submit_job(self, job: Job):
        """Submit the job specified by `job` to the system.

        Parameters
        ----------
        job : Job
            Job to submit
        """
        pass

    @abstractmethod
    def copy_from_template(self, source_drc: Path, target_drc: Path):
        """Copy from template directory `source_drc` to target directory
        `target_drc`

        Parameters
        ----------
        source_drc : Path
            Source directory
        target_drc : Path
            Target directory
        """
        pass

    @abstractmethod
    def imas_from_path(self, template_drc: Path) -> ImasHandle:
        """It takes a path, and finds out the IMAS entry associated with it.

        Parameters
        ----------
        template_drc : Path
            Folder from which to extract IMAS location

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
            Run directory
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
    ) -> ImasHandle:
        """Get handle for data input. This method is used to copy the template
        data to wherever the system expects the input data to be.

        Parameters
        ----------
        dirname : Path
            Run directory
        source : ImasHandle
            Template Imas data
        """
        pass

    @abstractmethod
    def get_data_out_handle(
        self,
        *,
        dirname: Path,
        source: ImasHandle,
    ) -> ImasHandle:
        """Get handle for data output. This method is used to set the locations
        in the system correct (later on), in a sense this method is
        superfluous.

        Parameters
        ----------
        dirname : Path
            Run directory
        source : ImasHandle
            Template Imas data
        """
        pass

    def submit_array(
        self,
        jobs: Sequence[Job],
        *,
        max_jobs: int = 10,
        max_array_size: int = 100,
        create_only: bool = False,
        **kwargs,
    ):
        """Submit the jobs in an array fashion, its perfectly fine to just
        throw an error if the system does not support it.

        Parameters
        ----------
        jobs : Sequence[Job]
            List of jobs to submit.
        max_jobs : int
            Maximum number of jobs at the same time.
        max_array_size : int
            Maximum slurm array size.
        create_only : bool
            If true, create array script, but do not submit
        kwargs : dict
            These keyword arguments are passed on to the system.
        """
        raise NotImplementedError('Array submission not implemented')
