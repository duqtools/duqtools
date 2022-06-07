from typing import Optional
from pydantic import BaseModel, DirectoryPath
import yaml
from logging import debug
from duqtools.submit import Submit_config
from duqtools.status import Status_config

class Config(BaseModel):
  """
  Config class containing all configs, is a singleton and can be used with
  import duqtools.config.Config as Cfg
  Cfg().<variable you want>
  """

  _instance = None

  #pydantic members
  submit    : Optional[Submit_config] = Submit_config()
  status    : Optional[Status_config] = Status_config()
  workspace : DirectoryPath
  force     : bool = False

  def __init__(self, filename=None):
    """
    Initialize with optional filename argument
    """
    if filename:
      with open(filename,'r') as f:
        datamap = yaml.safe_load(f)
        debug(datamap)
        BaseModel.__init__(self,**datamap)

  def __new__(cls, *args, **kwargs):
    # Make it a singleton
    if not Config._instance:
      Config._instance = object.__new__(cls)
    return Config._instance
