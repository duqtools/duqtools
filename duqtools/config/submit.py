from .basemodel import BaseModel


class SubmitConfig(BaseModel):
    """Submit_config.

    Config class for submitting jobs
    """

    submit_script_name: str = '.llcmd'
    status_file: str = 'jetto.status'
    out_file: str = 'jetto.out'
    in_file: str = 'jetto.in'
    submit_command: str = 'sbatch'
