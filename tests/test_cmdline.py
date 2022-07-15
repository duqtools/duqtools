import os
import shutil
import subprocess
from pathlib import Path

import pytest

from duqtools.utils import work_directory


@pytest.fixture(scope='session', autouse=True)
def extra_env():
    # Add required coverage env variable to each test
    os.environ['COVERAGE_PROCESS_START'] = str(Path.cwd() / 'setup.cfg')


@pytest.fixture(scope='session', autouse=True)
def collect_cov(cmdline_workdir):
    yield None
    # Executed at end of session, but before closure of cmdline_workdir
    for cov_file in cmdline_workdir.glob('.coverage.*'):
        shutil.copy(cov_file, Path.cwd())


@pytest.fixture(scope='session')
def cmdline_workdir(tmp_path_factory):
    # Create working directory for cmdline tests, and set up input files
    workdir = tmp_path_factory.mktemp('test_cmdline')
    (workdir / Path('workspace')).mkdir()
    shutil.copy(Path.cwd() / 'tests' / 'test_cmdline_config.yaml',
                workdir / 'config.yaml')
    shutil.copytree(Path.cwd() / 'example' / 'template_model',
                    workdir / Path('template_model'))
    return workdir


@pytest.mark.dependency()
def test_example_create(cmdline_workdir):
    cmd = 'duqtools create -c config.yaml --force'.split()

    with work_directory(cmdline_workdir):
        result = subprocess.run(cmd)
        assert (result.returncode == 0)


@pytest.mark.dependency(depends=['test_example_create'])
def test_example_submit(cmdline_workdir):
    cmd = 'duqtools submit -c config.yaml'.split()

    with work_directory(cmdline_workdir):
        result = subprocess.run(cmd)
        assert (result.returncode == 0)


@pytest.mark.dependency(depends=['test_example_create'])
def test_example_status(cmdline_workdir):
    cmd = 'duqtools status -c config.yaml'.split()

    with work_directory(cmdline_workdir):
        result = subprocess.run(cmd)
        assert (result.returncode == 0)


@pytest.mark.dependency(depends=['test_example_status'])
def test_example_plot(cmdline_workdir):
    cmd = 'duqtools plot -c config.yaml'.split()

    with work_directory(cmdline_workdir):
        result = subprocess.run(cmd)
        assert (result.returncode == 0)
        assert (Path('./plot_0000.png').exists())
