from pydantic import BaseModel
import duqtools.config
from logging import debug
from os import scandir

class Submit_config(BaseModel):
  nodes              : int
  processors         : int
  processors_per_case: int

def submit():
  cfg = duqtools.config.Config()
  if not cfg.submit:
    raise Exception("submit field required in config file")
  debug("Submit config: %s"%cfg.submit)

  case_dirs = [entry for entry in scandir(cfg.workspace) if entry.is_dir()]
  debug("Case directories: %s"%case_dirs)

