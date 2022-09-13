from __future__ import annotations

from typing import List, Tuple, Union

from pydantic import Field, validator
from typing_extensions import Literal

from ._basemodel import BaseModel
from ._description_helpers import formatter as f
from ._ranges import ARange, LinSpace
from ._variable import IDSVariableModel, JettoVariableModel


class OperatorMixin(BaseModel):
    operator: Literal['add', 'multiply', 'divide', 'power', 'subtract',
                      'floor_divide', 'mod', 'copyto',
                      'remainder'] = Field('multiply',
                                           description=f("""
        Which operator to apply to the data in combination with any of the
        given values below. This can be any of the basic numpy arithmetic
        operations. Available choices: `add`, `multiply`, `divide`, `power`,
        `subtract`, `floor_divide`, `mod`, `none` and `remainder`. These directly map
        to the equivalent numpy functions, i.e. `add` -> `np.add`.
        """))
    scale_to_error: bool = Field(False,
                                 description=f("""
        If True, multiply value(s) by the error (sigma).

        With asymmetric errors (i.e. both lower/upper error nodes are available),
        scale to the lower error node for values < 0, and to the upper error node
        for values > 0.
        """))

    _upper_suffix: str = '_error_upper'
    _lower_suffix: str = '_error_lower'


class DimMixin(BaseModel):
    values: Union[List[float], ARange, LinSpace] = Field([1.1, 1.2, 1.3],
                                                         description=f("""
            Values to use with operator on field to create sampling
            space."""))

    @validator('values')
    def convert_to_list(cls, v):
        if not isinstance(v, list):
            v = v.values
        return v


class OperationDim(OperatorMixin, DimMixin, BaseModel):
    variable: str = Field(description=f("""
    PlaceHolder for the actual Operator
    """))

    def expand(self, *args, **kwargs):
        from ..config import cfg
        variable = cfg.variables.to_variable_dict()[self.variable]
        if type(variable) == JettoVariableModel:
            return JettoOperationDim.expand(self,
                                            *args,
                                            variable=variable,
                                            **kwargs)
        elif type(variable) == IDSVariableModel:
            return IDSOperationDim.expand(self,
                                          *args,
                                          variable=variable,
                                          **kwargs)
        else:
            raise NotImplementedError(
                f'{self.variable} expand not implemented')


class CoupledDim(BaseModel):
    __root__: List[OperationDim]

    @validator('__root__')
    def check_dimensions_match(cls, dims):
        if len(dims) > 0:
            refdim = len(dims[0].values)
            for dim in dims[1:]:
                if not len(dim.values) == refdim:
                    raise ValueError('dimensions do not match in coupled dim')
        return dims

    def expand(self, *args, **kwargs):
        expanded = [operation.expand() for operation in self.__root__]
        return [entry for entry in zip(*expanded)]  # Transpose


########################
# IDS Specific
########################


class IDSPathMixin(BaseModel):
    variable: IDSVariableModel = Field(description=f("""
            IDS variable for the data to modify.
            The time slice can be denoted with '*', this will match all
            time slices in the IDS. Alternatively, you can specify the time
            slice directly, i.e. `profiles_1d/0/t_i_average` to only
            match and update the 0-th time slice.
            """))


class IDSOperation(IDSPathMixin, OperatorMixin, BaseModel):
    """Apply arithmetic operation to IDS."""

    value: float = Field(description=f("""
        Values to use with operator on field to create sampling
        space."""))


class IDSOperationDim(IDSPathMixin, OperatorMixin, DimMixin, BaseModel):
    """Apply set of arithmetic operations to IDS.

    Takes the IDS data and subtracts, adds, multiplies, etc with each
    the given values.
    """

    def expand(self, *args, variable, **kwargs) -> Tuple[IDSOperation, ...]:
        """Expand list of values into operations with its components."""
        return tuple(
            IDSOperation(variable=variable,
                         operator=self.operator,
                         value=value,
                         scale_to_error=self.scale_to_error)
            for value in self.values)


########################
# Jetto Specific
########################


class JettoPathMixin(BaseModel):
    variable: JettoVariableModel


class JettoOperation(JettoPathMixin, OperatorMixin, BaseModel):
    value: float = Field(description=f("""
        Values to use with operator on field to create sampling
        space."""))


class JettoOperationDim(JettoPathMixin, OperatorMixin, DimMixin, BaseModel):

    def expand(self, *args, variable, **kwargs) -> Tuple[JettoOperation, ...]:
        """Expand list of values into operations with its components."""
        return tuple(
            JettoOperation(variable=variable,
                           operator=self.operator,
                           value=value,
                           scale_to_error=self.scale_to_error)
            for value in self.values)
