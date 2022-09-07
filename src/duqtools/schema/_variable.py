from typing import List, Optional

from pydantic import Field

from ._basemodel import BaseModel
from ._description_helpers import formatter as f
from ._jetto import JettoVar


class VariableModel(BaseModel):
    pass


class JettoVariableModel(VariableModel):
    """Variable for describing variables specific to Jetto, These variables
    need to be defined as a lookup table lookup.json (jetto-pythontools), or in
    the jintrac_config_vars.yaml (jetto-duqtools). Otherwise there will be an
    error on accessing them.

    Issue #282 plans on adding lookup-table support to this variable
    """

    type: str = Field('jetto-variable',
                      description='discriminator for the variable type')

    name: str = Field(description=f("""
        Name of the variable
        Used for the lookup table to find actual fields
        """))
    lookup: Optional[JettoVar] = Field(description=f("""
    description of the fields that have to be updated for a Jetto Variable
    """))


class IDSVariableModel(VariableModel):
    """Variable for describing data within a IMAS database.

    The variable can be given a name, which will be used in the rest of the config
    to reference the variable. It will also be used as the column labels or
    on plots.

    The dimensions for each variable must be specified. This ensures the the data
    will be self-consistent. For example for 1D data, you can use `[x]` and for 2D data,
    `[x, y]`.

    The IDS path may contain indices. You can point to a single index, by simply giving the
    complete path (i.e. `profiles_1d/0/t_i_average` for the 0th time slice).
    To retrieve all time slices, you can use `profiles_1d/*/t_i_average`.
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
        The fields are separated by forward slashes (`\\`).
    """))
    dims: List[str] = Field(description=f("""
        Give the dimensions of the data,
        i.e. [x] for 1D, or [x, y] for 2D data.
    """))
