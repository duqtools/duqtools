from __future__ import annotations

from typing import Union

from pydantic import Field

from duqtools.schema import BaseModel, DimMixin, OperatorMixin
from duqtools.utils import formatter as f

from ._models import JettoVariableModel


class JettoPathMixin(BaseModel):
    variable: JettoVariableModel


class JettoOperation(JettoPathMixin, OperatorMixin, BaseModel):
    value: Union[float, list] = Field(description=f("""
        Value to use with operator on field to create sampling
        space."""))


class JettoOperationDim(JettoPathMixin, OperatorMixin, DimMixin, BaseModel):

    def expand(self, *args, variable, **kwargs) -> tuple[JettoOperation, ...]:
        """Expand list of values into operations with its components."""
        return tuple(
            JettoOperation(variable=variable,
                           operator=self.operator,
                           value=value,
                           scale_to_error=self.scale_to_error)
            for value in self.values)
