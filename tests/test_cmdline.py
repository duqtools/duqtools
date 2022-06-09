import os
import shutil
import subprocess
from pathlib import Path

import pytest

from duqtools.utils import work_directory


@pytest.fixture(scope='session')
def cmdline_workdir(tmp_path_factory):
    workdir = tmp_path_factory.mktemp('test_cmdline')
    (workdir / Path('workspace')).mkdir()
    shutil.copy(os.getcwd() + '/example/config.yaml', workdir)
    shutil.copytree(os.getcwd() + '/example/template_model',
                    workdir / Path('template_model'))
    return workdir


@pytest.mark.dependency()
def test_example_create(cmdline_workdir):
    with work_directory(cmdline_workdir):
        result = subprocess.run(['duqtools', 'create', 'config.yaml'])
        assert (result.returncode == 0)


@pytest.mark.dependency(depends=['test_example_create'])
def test_example_status(cmdline_workdir):
    with work_directory(cmdline_workdir):
        result = subprocess.run(['duqtools', 'status', 'config.yaml'])
        assert (result.returncode == 0)
