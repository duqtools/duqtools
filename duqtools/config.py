from typing import Optional
from pydantic import BaseModel
import yaml
from logging import debug
from duqtools.submit import Submit_config

config = None

class Config(BaseModel):
  submit: Optional[Submit_config]

  def __init__(self, filename):
    with open(filename,'r') as f:
      datamap = yaml.safe_load(f)
      debug(datamap)
      BaseModel.__init__(self,**datamap)
