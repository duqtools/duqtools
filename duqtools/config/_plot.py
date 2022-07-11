from typing import List, Optional

from pydantic import Field

from .basemodel import BaseModel


class Plot(BaseModel):
    x: Optional[str] = Field(
        'profiles_1d/0/grid/rho_tor',
        description='Data on x-axis, default is the toroidal flux coordiante')
    # TODO, make y axis time-variable by replacing "0" with "*" for example
    y: str = Field('profiles_1d/0/electrons/density_thermal',
                   description='Data on y-axis')

    xlabel: Optional[str] = Field(None, description='Custom label for x-axis')
    ylabel: Optional[str] = Field(None, description='Custom label for y-axis')

    def get_xlabel(self):
        return self.xlabel if self.xlabel else self.x

    def get_ylabel(self):
        return self.ylabel if self.ylabel else self.y


class PlotConfig(BaseModel):
    plots: List[Plot] = [Plot()]
