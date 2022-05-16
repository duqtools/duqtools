from pydantic import BaseModel
import duqtools.config as cfg

class Submit_config(BaseModel):
  time               :  str
  nodes              : int
  processors         : int
  processors_per_case: int

def submit():
  print(cfg.config.submit)
