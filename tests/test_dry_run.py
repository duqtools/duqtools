import os
import shutil
from pathlib import Path

import pytest

from duqtools.cli import cli_clean, cli_create, cli_init, cli_plot, cli_submit
from duqtools.utils import work_directory

pytest.importorskip('imas')  # These tests require imas to be installed


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
    shutil.copy(Path.cwd() / 'tests' / 'dry_run.yaml', workdir / 'config.yaml')
    shutil.copytree(Path.cwd() / 'example' / 'template_model',
                    workdir / Path('template_model'))
    return workdir


@pytest.mark.dependency()
def test_clean_database(cmdline_workdir):
    with work_directory(cmdline_workdir):
        cli_create(['-c', 'config.yaml', '--force', '--yes'],
                   standalone_mode=False)
        cli_clean(['-c', 'config.yaml', '--force', '--out', '--yes'],
                  standalone_mode=False)
        assert (not Path('./run_0000').exists())
        assert (not Path('./run_0001').exists())
        assert (not Path('./run_0002').exists())
        assert (not Path('./runs.yaml').exists())
        assert (Path('./runs.yaml.old').exists())


def test_init(cmdline_workdir):
    with work_directory(cmdline_workdir):
        cli_init(['--full', '--dry-run'], standalone_mode=False)
        assert (not Path('./duqtools.yaml').exists())


@pytest.mark.dependency(depends=['test_clean_database'])
def test_create(cmdline_workdir):
    with work_directory(cmdline_workdir):
        cli_create(['-c', 'config.yaml', '--dry-run', '--force'],
                   standalone_mode=False)
        assert (not Path('./run_0000').exists())
        assert (not Path('./run_0001').exists())
        assert (not Path('./run_0002').exists())
        assert (not Path('./runs.yaml').exists())


@pytest.mark.dependency(depends=['test_create'])
@pytest.mark.dependency()
def test_real_create(cmdline_workdir):
    with work_directory(cmdline_workdir):
        cli_create(['-c', 'config.yaml', '--force', '--yes'],
                   standalone_mode=False)
        assert (Path('./run_0000').exists())
        assert (Path('./run_0001').exists())
        assert (Path('./run_0002').exists())
        assert (Path('./runs.yaml').exists())


@pytest.mark.dependency(depends=['test_real_create'])
def test_submit(cmdline_workdir):
    with work_directory(cmdline_workdir):
        cli_submit(['-c', 'config.yaml', '--dry-run'], standalone_mode=False)
        assert (not Path('./run_0000/duqtools.lock').exists())
        assert (not Path('./run_0001/duqtools.lock').exists())
        assert (not Path('./run_0002/duqtools.lock').exists())


@pytest.mark.dependency(depends=['test_real_create'])
def test_plot(cmdline_workdir):
    with work_directory(cmdline_workdir):
        cli_plot([
            '-c',
            'config.yaml',
            '--dry-run',
            '-x',
            'profiles_1d/*/grid/rho_tor_norm',
            '-y',
            'profiles_1d/*/t_i_average',
            '--imas',
            'g2aho/jet/94875/1',
        ],
                 standalone_mode=False)
        assert (not Path('./chart.html').exists())
