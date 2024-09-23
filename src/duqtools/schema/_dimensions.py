from __future__ import annotations

import ast
from functools import partial
from typing import Any, Literal, Optional, Union

import numpy as np
from imas2xarray import Variable
from pydantic import Field, field_validator, model_validator

from duqtools.utils import formatter as f

from ._basemodel import BaseModel, RootModel
from ._ranges import ARange, LinSpace


class OperatorMixin(BaseModel):
    operator: Literal['add', 'multiply', 'divide', 'power', 'subtract',
                      'floor_divide', 'mod', 'copyto', 'remainder',
                      'custom'] = Field('multiply',
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

    clip_min: Optional[float] = Field(None,
                                      description=f("""
        If set, clip (limit) data at this value (upper bound).
        Uses `np.clip`.
        """))

    clip_max: Optional[float] = Field(None,
                                      description=f("""
        If set, clip (limit) data at this value (lower bound).
        Uses `np.clip`.
        """))

    linear_ramp: Optional[tuple[float, float]] = Field(None,
                                                       description=f("""
        Linearly ramp the operation using the start and stop value given.
        The first value (start) corresponds to multiplier at the beginning of the
        data range, the second value (stop) to the multiplier at the end.
        The ramp is linearly interpolated between the start and stop values.

        The linear ramp acts as a multiplier of the specified `value`.

        For example, for `operator: add`:
        `new_data = data + np.linspace(start, stop, len(data)) * value`
        """))

    input_variables: Optional[list[Any]] = Field(None,
                                                 description=f("""
        Input variables that should be present for a `operator: custom`
        operation. The values of this input variable can be used in the `custom_code`
        field.
    """))

    custom_code: Optional[str] = Field(None,
                                       description=f("""
        Custom python code to apply for the `custom` operator.
        This will be evaluated as if it were inline Python code.
        Two variables are accessible: `data` corresponds
        to the variable data, and `value` corresponds to pass value.

        The extra input_variables are defined in
        a dict named `var = { variable1 : value, variable2 : value}`

        For example, an implementation of `operator: multiply`:

        `custom_code: 'value * data'`

        Or an example of multiplying some input_variable named `key1`:
        `custom_code: `var['key1']*value`

        The resulting data must be of the same shape.
            """))

    _upper_suffix: str = '_error_upper'
    _lower_suffix: str = '_error_lower'

    @field_validator('custom_code')
    @classmethod
    def check_ast(cls, custom_code):
        if custom_code:
            ast.parse(custom_code)
        return custom_code

    @model_validator(mode='before')
    def check_custom(cls, values):
        if values.get(
                'operator') == 'custom' and not values.get('custom_code'):
            raise ValueError(
                'Missing `custom_code` field for `operator: custom')
        return values

    def _custom_function(self,
                         data: np.ndarray | float,
                         value,
                         *,
                         out: Optional[np.ndarray] = None,
                         code: str,
                         var: Any):
        """Mimick np.ufunc for custom functions."""
        if out is not None:
            out[:] = eval(code)
        else:
            out = eval(code)
        return out

    def npfunc(self,
               data: np.ndarray | float,
               value,
               *,
               out: Optional[np.ndarray] = None,
               var: Optional[Any] = None) -> Any:
        if self.operator == 'custom':
            assert self.custom_code
            npfunc = partial(self._custom_function,
                             code=self.custom_code,
                             var=var)
        else:
            npfunc = getattr(np, self.operator)

        # copyto is different, and does not like scalars
        if self.operator == 'copyto' and not isinstance(data, np.ndarray):
            if isinstance(value, type(data)):
                return value
            else:
                return data

        if out is not None:
            return npfunc(data, value, out=out)
        else:
            return npfunc(data, value)


class DimMixin(BaseModel):
    values: Union[list[float], ARange, LinSpace] = Field(description=f("""
            Values to use with operator on field to create sampling
            space."""))

    @field_validator('values')
    @classmethod
    def convert_to_list(cls, v):
        if not isinstance(v, list):
            v = v.values
        return v


class OperationDim(OperatorMixin, DimMixin, BaseModel):
    variable: str = Field(description=f("""
    PlaceHolder for the actual Operator
    """))

    def expand(self, *args, **kwargs):
        from duqtools.config import var_lookup
        variable = var_lookup[self.variable]

        from duqtools.systems.jetto import JettoOperationDim, JettoVariableModel

        if isinstance(variable, JettoVariableModel):
            expand_func = JettoOperationDim.expand
        elif isinstance(variable, Variable):
            expand_func = IDSOperationDim.expand
        else:
            raise NotImplementedError(
                f'{self.variable} expand not implemented')

        return expand_func(self, *args, variable=variable, **kwargs)


class CoupledDim(RootModel):
    root: list[OperationDim]

    @field_validator('root')
    @classmethod
    def check_dimensions_match(cls, dims):
        if len(dims) > 0:
            refdim = len(dims[0].values)
            for dim in dims[1:]:
                if not len(dim.values) == refdim:
                    raise ValueError('dimensions do not match in coupled dim')
        return dims

    def expand(self, *args, **kwargs):
        expanded = [operation.expand() for operation in self.root]
        return [entry for entry in zip(*expanded)]  # Transpose


class IDSPathMixin(BaseModel):
    variable: Variable = Field(description=f("""
            IDS variable for the data to modify.
            The time slice can be denoted with '*', this will match all
            time slices in the IDS. Alternatively, you can specify the time
            slice directly, i.e. `profiles_1d/0/t_i_ave` to only
            match and update the 0-th time slice.
            """))


class IDSOperation(IDSPathMixin, OperatorMixin, BaseModel):
    """Apply arithmetic operation to IDS."""

    value: float = Field(description=f("""
        Value to use with operator on field to create sampling
        space."""))


class IDSOperationDim(IDSPathMixin, OperatorMixin, DimMixin, BaseModel):
    """Apply set of arithmetic operations to IDS.

    Takes the IDS data and subtracts, adds, multiplies, etc with each
    the given values.
    """

    def expand(self, *args, variable, **kwargs) -> tuple[IDSOperation, ...]:
        """Expand list of values into operations with its components."""
        return tuple(
            IDSOperation(variable=variable,
                         operator=self.operator,
                         value=value,
                         scale_to_error=self.scale_to_error)
            for value in self.values)


class Operation(OperatorMixin, BaseModel):
    variable: str
    value: Union[float, list]

    def convert(self):
        """Expand variable and convert to correct type."""
        from duqtools.config import var_lookup
        variable = var_lookup[self.variable]

        from duqtools.systems.jetto import JettoOperation, JettoVariableModel

        if isinstance(variable, JettoVariableModel):
            cls = JettoOperation
        elif isinstance(variable, Variable):
            cls = IDSOperation
        else:
            raise NotImplementedError(
                f'{self.variable} convert not implemented')

        mapping = self.model_dump()
        mapping['variable'] = variable

        return cls(**mapping)
