import atexit
import logging
import subprocess as sp
import sys
from pathlib import Path

from importlib_resources import files
from PySide2 import QtCore, QtWebEngineWidgets, QtWidgets

logger = logging.getLogger(__name__)


def kill_server(p):
    # p.kill is not adequate
    sp.call(['taskkill', '/F', '/T', '/PID', str(p.pid)])


def start_dash_in_subprocess():
    dashboard_path = files('duqtools.data') / 'dash' / 'dash.py'
    workdir = Path('.').resolve()
    cmd = f'streamlit run {dashboard_path} --server.headless=True -- {workdir}'

    print(cmd)
    p = sp.Popen(cmd, stdout=sp.DEVNULL)
    print(f'Starting dashboard on pid={p.pid})')
    atexit.register(kill_server, p)


def dash(**kwargs):
    """Requires `conda install -c conda-forge pyside2`."""
    start_dash_in_subprocess()

    hostname = 'localhost'
    port = 8501

    app = QtWidgets.QApplication(sys.argv)
    view = QtWebEngineWidgets.QWebEngineView()

    view.load(QtCore.QUrl(f'http://{hostname}:{port}'))
    view.show()
    sys.exit(app.exec_())
