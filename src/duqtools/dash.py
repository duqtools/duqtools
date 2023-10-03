from __future__ import annotations

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
    from streamlit.web import cli as stcli

    dashboard_path = files('duqtools.dashboard') / 'Plotting.py'

    workdir = Path('.').resolve()

    sys.argv = [
        *('streamlit', 'run', str(dashboard_path)),
        *('--theme.base', 'light'),
        *('--theme.primaryColor', 'be5108'),
        *('--theme.secondaryBackgroundColor', 'ddedf8'),
        *('--browser.gatherUsageStats', 'false'),
        *('--', str(workdir)),
    ]

    logger.debug('Streamlit arguments %s', sys.argv)

    sys.exit(stcli.main())
