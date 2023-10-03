from __future__ import annotations

from typing import Literal

from pydantic import Field

from ..models import SystemModel


class Ets6SystemModel(SystemModel):
    name: Literal['ets6'] = Field(
        'ets6', description='Backend system to use. Set by ConfigModel.')

    submit_script_name: str = 'run.sh'

    kepler_module: str = Field(
        description='module name used in kepler load <module>')
    kepler_load: str = Field(
        description='module name used in kepler load <module>')
    ets_xml: str = Field(
        '$ITMWORK/ETS6.xml',
        description='ETS6.XML file to use, can include for example `$ITMWORK`')
