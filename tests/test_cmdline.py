import os
import shutil
import subprocess
from pathlib import Path

import pytest
from pytest_dependency import depends

from duqtools.utils import work_directory

config_file_name = 'config_jetto.yaml'
systems = ['jetto-duqtools', 'jetto-pythontools']


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


@pytest.fixture(scope='session', params=systems)
def system(request):
    return request.param


@pytest.fixture(scope='session')
def cmdline_workdir(tmp_path_factory, system):
    # Create working directory for cmdline tests, and set up input files
    workdir = tmp_path_factory.mktemp('test_cmdline_{system}')
    shutil.copytree(Path.cwd() / 'example' / 'template_model',
                    workdir / 'template_model')

    with open(Path.cwd() / 'tests' / config_file_name, 'r') as fi:
        with open(workdir / 'config.yaml', 'w') as fo:
            fo.write(fi.read())
            fo.write(f'\nsystem: {system}')
    return workdir


@pytest.mark.dependency()
def test_example_create(cmdline_workdir):
    cmd = 'duqtools create -c config.yaml --force --yes'.split()

    with work_directory(cmdline_workdir):
        result = subprocess.run(cmd)
        assert (result.returncode == 0)


@pytest.mark.dependency()
def test_example_submit(cmdline_workdir, system, request):
    depends(request, [f'test_example_create[{system}]'])

    if system == 'jetto-pythontools':
        pytest.xfail('Prominence system does not yet work')

    cmd = 'duqtools submit -c config.yaml --yes'.split()

    with work_directory(cmdline_workdir):
        result = subprocess.run(cmd)
        assert (result.returncode == 0)


@pytest.mark.dependency()
def test_example_status(cmdline_workdir, system, request):
    depends(request, [f'test_example_create[{system}]'])

    cmd = 'duqtools status -c config.yaml --yes'.split()

    with work_directory(cmdline_workdir):
        result = subprocess.run(cmd)
        assert (result.returncode == 0)


@pytest.mark.dependency()
@pytest.mark.skip(reason='Should be fixed')
def test_example_plot(cmdline_workdir):
    cmd = 'duqtools plot -c config.yaml --yes'.split()

    with work_directory(cmdline_workdir):
        result = subprocess.run(cmd)
        assert (result.returncode == 0)
        assert (Path('./plot_0000.png').exists())
