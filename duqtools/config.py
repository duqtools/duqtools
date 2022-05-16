from pydantic import BaseModel
import yaml

class Config(BaseModel):
  test: str

  def __init__(self, filename):
    with open(filename,'r') as f:
      datamap = yaml.safe_load(f)
      print(datamap)
      BaseModel.__init__(self,**datamap)
