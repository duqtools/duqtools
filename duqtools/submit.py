from pydantic import BaseModel
import duqtools.config as cfg

class Submit_config(BaseModel):
  time               :  str
  nodes              : int
  processors         : int
  processors_per_case: int

def submit():
  if not cfg.config.submit:
    raise Exception("submit field required in config file")
  print(cfg.config.submit)
