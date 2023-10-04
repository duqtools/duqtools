from __future__ import annotations

import numpy as np
from pydantic import Field

from ._basemodel import BaseModel


class LinSpace(BaseModel):
    """Generated evenly spaced numbers over a specified interval.

    See the implementation of [numpy.linspace][] for more details.
    """
    start: float = Field(description='Start value of the sequence.')
    stop: float = Field(description='End value of the sequence.')
    num: int = Field(description='Number of samples to generate.')

    @property
    def values(self):
        """Convert to list."""
        # `val.item()` converts to native python types
        return [
            val.item() for val in np.linspace(self.start, self.stop, self.num)
        ]


class ARange(BaseModel):
    """Generate evenly spaced numbers within a given interval.

    See the implementation of [numpy.arange][] for more details.
    """

    start: float = Field(
        description='Start of the interval. Includes this value.')
    stop: float = Field(
        description='End of the interval. Excludes this interval.')
    step: float = Field(description='Spacing between values.')

    @property
    def values(self):
        """Convert to list."""
        # `val.item()` converts to native python types
        return [
            val.item() for val in np.arange(self.start, self.stop, self.step)
        ]
