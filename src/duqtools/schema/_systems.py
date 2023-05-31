from typing import Literal

from pydantic import Field

from ._basemodel import BaseModel


class Ets6SystemModel(BaseModel):
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


class DummySystemModel(BaseModel):
    name: Literal['dummy'] = 'dummy'
    submit_script_name: str = 'true'


class JettoSystemModel(BaseModel):
    name: Literal['jetto', 'jetto-v210921', 'jetto-v220922'] = 'jetto'
    submit_script_name: str = '.llcmd'
