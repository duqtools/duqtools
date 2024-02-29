from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from duqtools.operations import add_to_op_queue

from ..base_system import AbstractSystem
from ._schema import NoSystemModel

if TYPE_CHECKING:
    from duqtools.api import ImasHandle


class NoSystem(AbstractSystem):
    """This system is intended for workflows that need to apply some operations
    or sampling of the data without any system.

    With this system, you won't have to specify `create.template`. Only
    `create.template_data` is required.

    ```yaml title="duqtools.yaml"
    system:
      name: 'nosystem'  # or `name: None`
    ```
    """
    model: NoSystemModel

    def get_runs_dir(self) -> Path:
        assert self.cfg.create
        runs_dir = self.cfg.create.runs_dir

        if runs_dir:
            return runs_dir

        count = 0
        while True:  # find the next free folder
            dirname = f'duqtools_data_{count:04d}'
            if not (Path() / dirname).exists():
                break
            count = count + 1

        return Path() / dirname

    def write_batchfile(*args, **kwargs):
        pass

    @add_to_op_queue('Copying template to', '{target_drc}', quiet=True)
    def copy_from_template(self, source_drc: Path, target_drc: Path):
        shutil.copytree(source_drc, target_drc, dirs_exist_ok=True)

    def update_imas_locations(*args, **kwargs):
        pass

    def submit_job(*args, **kwargs):
        raise NotImplementedError(
            'Not yet implemented, please submit your jobs manually`')

    def imas_from_path(*args, **kwargs):
        raise NotImplementedError(
            """We cannot determine the input imas from a path,
               please specify `create->template_data`""")

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
        from duqtools.ids import ImasHandle

        relative_location: Optional[str] = str(
            os.path.relpath((dirname / 'imasdb').resolve()))
        if relative_location:
            if relative_location.startswith('..'):
                relative_location = None
        return ImasHandle(user=str((dirname / 'imasdb').resolve()),
                          db=source.db,
                          shot=source.shot,
                          run=source.run,
                          relative_location=relative_location)

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
        from duqtools.ids import ImasHandle

        relative_location: Optional[str] = str(
            os.path.relpath((dirname / 'imasdb').resolve()))
        if relative_location:
            if relative_location.startswith('..'):
                relative_location = None
        return ImasHandle(user=str((dirname / 'imasdb').resolve()),
                          db=source.db,
                          shot=source.shot,
                          run=source.run,
                          relative_location=relative_location)
