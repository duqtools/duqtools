from __future__ import annotations

import logging
import os
import re
from getpass import getuser
from typing import TYPE_CHECKING

from pydantic import field_validator

from ._schema import ImasBaseModel

if TYPE_CHECKING:

    pass

logger = logging.getLogger(__name__)

IMAS_PATTERN = re.compile(
    r'^((?P<user>[\\\/\w]*)\/)?(?P<db>\w+)\/(?P<shot>\d+)\/(?P<run>\d+)$')


class ImasBaseHandle(ImasBaseModel):

    def __str__(self):
        return f'{self.user}/{self.db}/{self.shot}/{self.run}'

    @classmethod
    def from_string(cls, string: str) -> ImasBaseHandle:
        """Return location from formatted string.

        Format:

            <user>/<db>/<shot>/<run>
            <db>/<shot>/<run>

        Default to the current user if the user is not specified.

        For example:

            g2user/jet/91234/555

        Parameters
        ----------
        string : str
            Input string containing imas db path

        Returns
        -------
        ImasHandle
        """
        match = IMAS_PATTERN.match(string)

        if match:
            return cls(**match.groupdict())

        raise ValueError(f'Could not match {string!r}')

    @field_validator('user')
    def user_rel_path(cls, v, values):
        # Override user if we have a relative location
        if relative_location := values.data['relative_location']:
            logger.info(
                f'Updating imasdb location with relative location {relative_location}'
            )
            return os.path.abspath(relative_location)
        return v

    def validate(self):
        """Validate the user.

        If the user is a path, then create it.

        Raises
        ------
        ValueError:
            If the user is invalid.
        """
        if self.is_local_db:
            # jintrac v220922
            self.path().parent.mkdir(parents=True, exist_ok=True)
        elif self.user == getuser() or self.user == 'public':
            # jintrac v210921
            pass
        else:
            raise ValueError(f'Invalid user: {self.user}')

    def to_string(self) -> str:
        """Generate string representation of Imas location."""
        return f'{self.user}/{self.db}/{self.shot}/{self.run}'

    @property
    def is_local_db(self):
        """Return True if the handle points to a local imas database."""
        return self.user.startswith('/')
