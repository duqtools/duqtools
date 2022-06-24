from typing import List, Optional

from .basemodel import BaseModel


class Plot(BaseModel):
    x: Optional[str]
    # TODO, make y axis time-variable by replacing "0" with "*" for example
    y: str = 'profiles_1d/0/electrons/density_thermal'

    xlabel: Optional[str]
    ylabel: Optional[str]

    add_time_slider: bool = False

    def get_xlabel(self):
        return self.xlabel if self.xlabel else self.x

    def get_ylabel(self):
        return self.ylabel if self.ylabel else self.y


class PlotConfig(BaseModel):
    plots: List[Plot] = [Plot()]
