import logging
import sys
from pathlib import Path

from streamlit import cli as stcli

logger = logging.getLogger(__name__)


def dash(**kwargs):
    """Start streamlit dashboard."""
    dashboard_path = Path(__file__).parents[1] / 'dash' / 'dash.py'
    workdir = Path('.').resolve()

    sys.argv = ['streamlit', 'run', str(dashboard_path), '--', str(workdir)]

    logger.debug('Streamlit arguments %s', sys.argv)

    sys.exit(stcli.main())
