from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, List, Optional, Type

from pydantic import BaseModel, validator
from pydantic_yaml import YamlModelMixin
from typing_extensions import Literal

from duqtools.api import ImasHandle

from ..types import PathLike
from ._jetto_in import JettoIn
from ._jetto_jset import JettoJset


class JettoField(BaseModel):
    file: Literal['jetto.jset', 'jetto.in']
    field: str
    section: Optional[str] = None

    @validator('section')
    def section_lower(cls, v):
        return v.lower()


class JettoVar(BaseModel):
    doc: str
    name: str
    type: Type
    keys: List[JettoField]

    @validator('type', pre=True)
    def validate_type(cls, v):
        return {
            'str': str,
            'int': int,
            'float': float,
        }[v]


class JettoConfigModel(YamlModelMixin, BaseModel):
    __root__: List[JettoVar] = []

    def __iter__(self):
        yield from self.__root__

    def __getitem__(self, index: int):
        return self.__root__[index]


cfg_path = Path(__file__).parent / 'jintrac_config_vars.yaml'

CONFIG = JettoConfigModel.parse_file(cfg_path)


class JettoSettingsManager:

    def __init__(self):
        self.handlers = {}

    def __new__(cls, *args, **kwargs):

        def setter(keys: List[JettoField]):

            def f(self, value):
                for key in keys:

                    cfg_file = key.file
                    field = key.field
                    section = key.section

                    self.handlers[cfg_file].set(field, value, section=section)

            return f

        def getter(key: Any, setting_type):

            def f(self):

                cfg_file = key.file
                field = key.field
                section = key.section

                value = self.handlers[cfg_file].get(field, section=section)

                return setting_type(value)

            return f

        for variable in CONFIG:
            name = variable.name
            doc = variable.doc
            keys = variable.keys

            setting_type = variable.type

            prop = property(
                fget=getter(keys[0], setting_type),
                fset=setter(keys),
                doc=doc,
            )
            setattr(cls, name, prop)

        return super().__new__(cls)

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
