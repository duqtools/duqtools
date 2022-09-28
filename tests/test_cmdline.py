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
def test_example_plot(cmdline_workdir):
    from duqtools.ids import imas_mocked
    if imas_mocked:
        pytest.xfail('Imas needed for plotting Imas data')

    cmd = ('duqtools plot -c config.yaml -m g2vazizi/test/94875/8000'
           ' -y profiles_1d/*/t_i_average').split()

    with work_directory(cmdline_workdir):
        result = subprocess.run(cmd)
        assert (result.returncode == 0)
        assert (Path('./chart_0.html').exists())


def test_create_missing_sanco_input(cmdline_workdir, system, tmp_path):
    pytest.xfail('we dont have an input file without sanco for'
                 ' jetto-pythontools (yet) to test')

    shutil.copytree(cmdline_workdir, tmp_path / 'run')
    os.remove(tmp_path / 'run' / 'template_model' / 'jetto.sin')

    cmd = 'duqtools create -c config.yaml --force --yes'.split()

    with work_directory(tmp_path / 'run'):
        result = subprocess.run(cmd)
        assert (result.returncode == 0)
