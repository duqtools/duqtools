from pydantic import BaseModel
import yaml
from logging import debug

class Config(BaseModel):
  test: str

  def __init__(self, filename):
    with open(filename,'r') as f:
      datamap = yaml.safe_load(f)
      debug(datamap)
      BaseModel.__init__(self,**datamap)
