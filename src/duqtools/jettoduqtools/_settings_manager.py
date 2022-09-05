"""The JettoSettingsManager is a single access point for multiple configs.

In the Jetto system, there are two config files, `jetto.in` and `jetto.jset`
that contain some settings that should be kept synchronized. Within
jetto.jset there are several fields that should map to the same value.

The settings manager consolidates fields that should have the same value
to a single variable. For example, the attribute `shot_in` referring to the
shot number, can map to 4 fields in `jetto.jset` and 1 in `jetto.in`.

These fields are configured in the file:
`duqtools/data/jintrac_config_vars.yaml`.

Each entry contains the `name` the field(s) are exposed as,
some documentation (`doc`), the `type` of the variable,
and the `keys`. Each key has it's field name (`field`) and
`file` in which the variable can be found associated with it.
It can also have a `section` if the field is not at the root level.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import List

from importlib_resources import files

from duqtools.api import ImasHandle

from .._types import PathLike
from ._jetto_in import JettoIn
from ._jetto_jset import JettoJset
from ._settings_manager_schema import JettoConfigModel, JettoField

CFG_PATH = files('duqtools.data') / 'jintrac_config_vars.yaml'
CONFIG = JettoConfigModel.parse_file(CFG_PATH)


class JettoSettingsManager:

    def __init__(self):
        self.handlers = {}

    def __new__(cls, *args, **kwargs):

        def setter(keys: List[JettoField]):

            def f(self, value):
                for key in keys:
                    entry = self.handlers[key.file]
                    entry.set(key.field, value, section=key.section)

            return f

        def getter(key: JettoField, setting_type: type):

            def f(self):
                entry = self.handlers[key.file]
                value = entry.get(key.field, section=key.section)

                return setting_type(value)

            return f

        for variable in CONFIG:
            prop = property(
                fget=getter(variable.keys[0], variable.type),
                fset=setter(variable.keys),
                doc=variable.doc,
            )
            setattr(cls, variable.name, prop)

        return super().__new__(cls)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __setitem__(self, key: str, value):
        setattr(self, key, value)

    def copy(self):
        """Return a copy of this instance."""
        return deepcopy(self)

    def set_imas_locations(self, inp: ImasHandle,
                           out: ImasHandle) -> JettoSettingsManager:
        """Make a copy with updated IDS locations for input / output.

        Parameters
        ----------
        inp : ImasHandle
            IMAS description of where the input data is stored.
        out : ImasHandle
            IMAS description of where the output data should be stored.

        Returns
        -------
        jset_new : JettoSettingsManager
            Copy of the jetto settings with updated IDS locations.
        """
        jset_new = self.copy()

        jset_new.user_in = inp.user
        jset_new.machine_in = inp.db
        jset_new.shot_in = inp.shot
        jset_new.run_in = inp.run

        jset_new.machine_out = out.db
        jset_new.shot_out = out.shot
        jset_new.run_out = out.run

        return jset_new

    @classmethod
    def from_directory(cls, path: PathLike) -> JettoSettingsManager:
        """Read Jetto settings from config files in directory.

        The config files are `jetto.in` and `jetto.jset`

        Parameters
        ----------
        path : PathLike
            Path to directory containing `jetto.jset`

        Returns
        -------
        jset : JettoSettingsManager
            Instance of `JettoSettingsManager`
        """
        path = Path(path)

        jsetmanager = cls()

        jjset = JettoJset.from_directory(path)
        jsetmanager.register(jjset.DEFAULT_FILENAME, jjset)

        jin = JettoIn.from_directory(path)
        jsetmanager.register(jin.DEFAULT_FILENAME, jin)

        return jsetmanager

    def to_directory(self, directory: PathLike):
        """Write a new `jetto.jset` / `jetto.in` to the given directory.

        Parameters
        ----------
        directory : PathLike
            Name of output directory
        """
        for name, handler in self.handlers.items():
            handler.to_directory(directory)

    def register(self, filename: str, handler):
        """Register config handlers.

        Parameters
        ----------
        filename : str
            Filename that is handled by this handler.
        handler : TYPE
            The config handler.
        """
        self.handlers[filename] = handler
