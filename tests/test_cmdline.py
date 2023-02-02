import os
import shutil
import subprocess as sp
from pathlib import Path

import click
import pytest
from pytest import TEST_DATA
from pytest_dependency import depends

from duqtools.utils import work_directory

imas = pytest.importorskip('imas',
                           reason='No way of testing this without IMAS')

config_file_name = 'config_jetto.yaml'
systems = ['jetto-v220922', 'jetto-v210921']


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
    workdir = tmp_path_factory.mktemp(f'test_cmdline_{system}')
    shutil.copytree(TEST_DATA / 'template_model', workdir / 'template_model')

    with open(TEST_DATA / config_file_name) as fi:
        with open(workdir / 'config.yaml', 'w') as fo:
            fo.write(fi.read())
            fo.write(f'\nsystem: {system}')
    yield workdir

    if system == 'v210921':
        for i in range(3):
            p = Path(cmdline_workdir,
                     f'run_000{i}/imasdb/test/3/0/ids_111110001.datafile')
            p.unlink()


@pytest.mark.dependency()
def test_example_create(cmdline_workdir, system):
    cmd = 'duqtools create -c config.yaml --force --yes'.split()

    with work_directory(cmdline_workdir):
        result = sp.run(cmd)
        assert (result.returncode == 0)

        for i in range(3):
            if system == 'jetto-v210921':
                p = Path(
                    f'/opt/imas/shared/imasdb/test/3/0/ids_90350000{i}.datafile'
                )
            else:
                p = Path(cmdline_workdir,
                         f'run_000{i}/imasdb/test/3/0/ids_903500001.datafile')
            assert p.exists()


@pytest.mark.dependency()
def test_example_recreate(cmdline_workdir, system):
    cmd = 'duqtools recreate run_0000 -c config.yaml --yes'.split()

    if system == 'jetto-v210921':
        p = Path('/opt/imas/shared/imasdb/test/3/0/ids_903507000.datafile')
    else:
        p = Path(cmdline_workdir,
                 'run_0000/imasdb/test/3/0/ids_903500001.datafile')

    p.unlink()
    assert not p.exists()

    with work_directory(cmdline_workdir):
        result = sp.run(cmd)
        assert (result.returncode == 0)

        assert p.exists()


@pytest.mark.dependency()
def test_example_submit(cmdline_workdir, system, request):
    depends(request, [f'test_example_create[{system}]'])

    cmd = 'duqtools submit -c config.yaml --yes'.split()

    with work_directory(cmdline_workdir):
        result = sp.run(cmd)
        assert (result.returncode == 0)


@pytest.mark.dependency()
def test_example_resubmit(cmdline_workdir, system, request):
    depends(request, [f'test_example_submit[{system}]'])

    cmd = 'duqtools submit -c config.yaml --resubmit run_0000 --yes'.split()

    with work_directory(cmdline_workdir):
        result = sp.run(cmd)
        assert (result.returncode == 0)


@pytest.mark.dependency()
def test_example_submit_array(cmdline_workdir, system, request):
    depends(request, [f'test_example_submit[{system}]'])

    cmd = 'duqtools submit --array -c config.yaml --yes --force'.split()

    with work_directory(cmdline_workdir):
        result = sp.run(cmd)
        assert (result.returncode == 0)
        assert (Path('duqtools_slurm_array.sh').exists())


@pytest.mark.dependency()
def test_example_status(cmdline_workdir, system, request):
    depends(request, [f'test_example_create[{system}]'])

    cmd = 'duqtools status -c config.yaml --yes'.split()

    with work_directory(cmdline_workdir):
        result = sp.run(cmd)
        assert (result.returncode == 0)


def test_example_plot(cmdline_workdir):
    from duqtools.ids import imas_mocked
    if imas_mocked:
        pytest.xfail('Imas needed for plotting Imas data')

    cmd = ('duqtools plot -h public/jet/90350/2 -v zeff').split()

    with work_directory(cmdline_workdir):
        result = sp.run(cmd)
        assert (result.returncode == 0)
        assert (Path('./chart_rho_tor_norm-zeff.html').exists())


def test_create_missing_sanco_input(cmdline_workdir, system, tmp_path):
    pytest.xfail('we dont have an input file without sanco for'
                 ' jetto-pythontools (yet) to test')

    shutil.copytree(cmdline_workdir, tmp_path / 'run')
    os.remove(tmp_path / 'run' / 'template_model' / 'jetto.sin')

    cmd = 'duqtools create -c config.yaml --force --yes'.split()

    with work_directory(tmp_path / 'run'):
        result = sp.run(cmd)
        assert (result.returncode == 0)


def test_list_variables(cmdline_workdir):
    cmd = ('duqtools list-variables -c config.yaml').split()

    with work_directory(cmdline_workdir):
        result = sp.run(cmd, capture_output=True)
        assert (result.returncode == 0)

    out = click.unstyle(result.stdout.decode())
    err = click.unstyle(result.stderr.decode())

    assert err == ''
    assert 'IDS-variable' in out
    assert 'jetto-variable' in out
    assert '*my_extra_var' in out
    assert 'rho_tor_norm' in out
