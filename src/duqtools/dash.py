import logging
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    from importlib_resources import files
else:
    from importlib.resources import files

logger = logging.getLogger(__name__)


def dash(**kwargs):
    """Start streamlit dashboard."""
    try:
        from streamlit.web import cli as stcli
    except ImportError:
        # versions <= (1.11)
        from streamlit import cli as stcli

    dashboard_path = files('duqtools.data') / 'dash' / 'dash.py'

    workdir = Path('.').resolve()

    sys.argv = ['streamlit', 'run', str(dashboard_path), '--', str(workdir)]

    logger.debug('Streamlit arguments %s', sys.argv)

    sys.exit(stcli.main())
