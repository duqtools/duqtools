from __future__ import annotations

import logging
from copy import deepcopy
from pathlib import Path
from typing import Dict, List

from .._types import PathLike
from ._namelist import read_namelist, write_namelist

logger = logging.getLogger(__name__)


class JettoIn:
    DEFAULT_FILENAME = 'jetto.in'

    def __init__(self,
                 mapping: Dict[str, Dict[str, str]],
                 header: List[str] = None):
        self.raw_mapping = mapping
        self.header = header

    def get(self, field: str, section: str):
        return self.raw_mapping[section][field]

    def set(
        self,
        field: str,
        value: str,
        section: str,
    ):
        self.raw_mapping[section][field] = value

    def copy(self):
        """Return a copy of this instance."""
        return deepcopy(self)

    @classmethod
    def from_file(cls, path: PathLike) -> JettoIn:
        """Read JettoIn from 'jetto.in' file.

        Parameters
        ----------
        path : PathLike
            Path to `jetto.in`

        Returns
        -------
        jetto_in : JettoIn
            Instance of `JettoIn`
        """
        header, mapping = read_namelist(path)
        jetto_in = cls(mapping, header=header)
        return jetto_in

    @classmethod
    def from_directory(cls, path: PathLike) -> JettoIn:
        """Read JettoIn from 'jetto.in' file in given directory.

        Parameters
        ----------
        path : PathLike
            Path to directory containing `jetto.in`

        Returns
        -------
        jetto_in : JettoIn
            Instance of `JettoIn`
        """
        filename = Path(path) / cls.DEFAULT_FILENAME
        return cls.from_file(filename)

    def to_directory(self, directory: PathLike):
        """Write a new jetto.in to the given directory.

        Parameters
        ----------
        directory : PathLike
            Name of output directory
        """
        directory = Path(directory)

        filename = directory / self.DEFAULT_FILENAME

        write_namelist(filename,
                       self.raw_mapping,
                       header=self.header,
                       force=True)

        logger.debug('write %s', filename)
