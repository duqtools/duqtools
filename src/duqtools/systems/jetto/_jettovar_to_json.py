from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ._models import JsetField, NamelistField

if TYPE_CHECKING:
    from ..schema import JettoVar


def jettovar_to_json(variable: JettoVar):
    jsetfields = []
    nmlfields = []
    for field in variable.keys:
        if isinstance(field, JsetField):
            jsetfields.append(field)
        elif isinstance(field, NamelistField):
            nmlfields.append(field)
        else:
            raise NotImplementedError(f'unknown Jetto field type {field}')

    if len(nmlfields) > 1:
        raise RuntimeError(
            f'jetto_tools only support a single nml entry: {nmlfields}')

    var_dict = {'type': variable.type, 'dimension': variable.dimension}
    if var_dict['type'] == 'float':
        var_dict['type'] = 'real'
    if var_dict['dimension'] is None:
        var_dict['dimension'] = 'scalar'

    if len(jsetfields) > 0:
        var_dict['jset_id'] = jsetfields[0].field
    if len(jsetfields) > 1:
        var_dict['jset_flex_id'] = []  # type: ignore
        for field in jsetfields[1:]:
            var_dict['jset_flex_id'].append(field.field)  # type: ignore

    if len(nmlfields) == 1:
        var_dict['nml_id'] = {  # type: ignore
            'namelist': nmlfields[0].section,
            'field': nmlfields[0].field
        }

    return json.dumps({variable.name: var_dict})
