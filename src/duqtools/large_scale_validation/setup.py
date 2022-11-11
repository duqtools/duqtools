import logging
from pathlib import Path
from string import Template

from .config import Config
from .utils import read_imas_handles_from_file

logger = logging.getLogger(__name__)


def setup(*, template_file, input_file, runs_dir, **kwargs):
    runs_dir = Path(runs_dir)
    cwd = Path.cwd()

    handles = read_imas_handles_from_file(input_file)

    with open(template_file) as f:
        template = Template(f.read())

    for name, handle in handles.items():
        cfg = template.substitute(
            TEMPLATE_USER=handle.user,
            TEMPLATE_DB=handle.db,
            TEMPLATE_SHOT=handle.shot,
            TEMPLATE_RUN=handle.run,
            RUNS_DIR=runs_dir / name,
        )

        Config.parse_raw(cfg)

        out_drc = cwd / name
        out_drc.mkdir(exist_ok=False)

        with open(out_drc / 'duqtools.yaml', 'w') as f:
            f.write(cfg)
