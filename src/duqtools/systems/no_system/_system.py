from __future__ import annotations

import os
from pathlib import Path

from ..base_system import AbstractSystem
from ..jintrac import V220922Mixin
from ._schema import NoSystemModel


class NoSystem(V220922Mixin, AbstractSystem):
    """This system is intended for workflows that need to apply some operations
    or sampling of the data without any system like Jetto or ETS in mind.

    With this system, you won't have to specify `create.template`. Only
    `create.template_data` is required.

    ```yaml title="duqtools.yaml"
    system:
      name: 'nosystem'  # or `name: None`
    ```
    """
    model: NoSystemModel

    @property
    def jruns_path(self) -> Path:
        """Return the Path specified in the `$JRUNS` environment variable, or,
        if `$JRUNS` does not exists, return the current directory `./`.

        Returns
        -------
        Path
        """
        if jruns_env := os.getenv('JRUNS'):
            return Path(jruns_env)
        else:
            return Path()

    def get_runs_dir(self) -> Path:
        path = self.jruns_path

        assert self.cfg.create
        runs_dir = self.cfg.create.runs_dir

        if runs_dir:
            return path / runs_dir

        abs_cwd = str(Path.cwd().resolve())
        abs_jruns = str(path.resolve())

        # Check if jruns is parent dir of current dir
        if abs_cwd.startswith(abs_jruns):
            return path

        count = 0
        while True:  # find the next free folder
            dirname = f'duqtools_data_{count:04d}'
            if not (path / dirname).exists():
                break
            count = count + 1

        return path / dirname

    def write_batchfile(*args, **kwargs):
        pass

    def copy_from_template(*args, **kwargs):
        pass

    def update_imas_locations(*args, **kwargs):
        pass

    def submit_array(*args, **kwargs):
        pass

    def submit_job(*args, **kwargs):
        pass

    def imas_from_path(*args, **kwargs):
        pass
