import logging
import sys
from pathlib import Path

from importlib_resources import files

logger = logging.getLogger(__name__)


def dash(**kwargs):
    """Start streamlit dashboard."""
    from streamlit import cli as stcli

    dashboard_path = files('duqtools.data') / 'dash' / 'dash.py'

    workdir = Path('.').resolve()

    sys.argv = ['streamlit', 'run', str(dashboard_path), '--', str(workdir)]

    logger.debug('Streamlit arguments %s', sys.argv)

    sys.exit(stcli.main())
