from typing import List, Optional

from pydantic import Field

from ._description_helpers import formatter as f
from .basemodel import BaseModel


class Plot(BaseModel):
    """Description of the plot to produce."""
    x: Optional[str] = Field('profiles_1d/0/grid/rho_tor_norm',
                             description=f("""
        IDS of the data to plot on the x-axis, default is rho toroidal norm.
        """))

    # TODO, make y axis time-variable by replacing "0" with "*" for example
    y: str = Field('profiles_1d/0/electrons/density_thermal',
                   description='IDS of the data to plot on the y-axis')

    xlabel: Optional[str] = Field(None, description='Custom label for x-axis')
    ylabel: Optional[str] = Field(None, description='Custom label for y-axis')

    def get_xlabel(self):
        return self.xlabel if self.xlabel else self.x

    def get_ylabel(self):
        return self.ylabel if self.ylabel else self.y


class PlotConfig(BaseModel):
    """The options of the plot subcommand are stored under the `plot` key in
    the config.

    Plots are specified as a list under the `plots` key. Multiple plots
    can be defined, and they will be written sequentially as .png files
    to the current working directory.
    """
    plots: List[Plot] = [
        Plot(),
        Plot(
            x='profiles_1d/0/grid/rho_tor_norm',
            y='profiles_1d/0/t_i_average',
            xlabel='Rho tor.',
            ylabel='Ion temperature',
        )
    ]
