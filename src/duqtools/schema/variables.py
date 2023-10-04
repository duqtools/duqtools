from __future__ import annotations

from pydantic import Field

from duqtools.utils import formatter as f

from ._basemodel import BaseModel


class IDSPath(BaseModel):
    ids: str = Field(description='Root IDS name.')
    path: str = Field(description=f("""
        Path to the data within the IDS.
        The fields are separated by forward slashes (`\\`).
    """))


class IDSVariableModel(IDSPath):
    """Variable for describing data within a IMAS database.

    The variable can be given a name, which will be used in the rest of
    the config to reference the variable. It will also be used as the
    column labels or on plots.

    The dimensions for each variable must be specified. This ensures the
    the data will be self-consistent. For example for 1D data, you can
    use `[x]` and for 2D data, `[x, y]`.

    The IDS path may contain indices. You can point to a single index,
    by simply giving the complete path (i.e. `profiles_1d/0/t_i_ave` for
    the 0th time slice). To retrieve all time slices, you can use
    `profiles_1d/*/t_i_ave`.
    """
    type: str = Field('IDS-variable',
                      description='discriminator for the variable type')

    name: str = Field(description=f("""
        Name of the variable.
        This will be used to reference this variable.
    """))
    ids: str = Field(description='Root IDS name.')
    path: str = Field(description=f("""
        Path to the data within the IDS.
        The fields are separated by forward slashes (`/`).
    """))
    dims: list[str] = Field(description=f("""
        Give the dimensions of the data,
        i.e. [x] for 1D, or [x, y] for 2D data.
    """))
