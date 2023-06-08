import os
import shutil
import tempfile
from pathlib import Path

import pytest

from duqtools.api import create, get_status, recreate, submit

# from duqtools.api import status

imas = pytest.importorskip('imas',
                           reason='No way of testing this without IMAS')

TEMPLATE_MODEL = Path(
    __file__).parent.resolve() / 'test_data' / 'template_model'
CONTAINERIZED_RUNS_DIR = os.environ['CONTAINERIZED_RUNS_DIR']
IMASDB = Path(CONTAINERIZED_RUNS_DIR).resolve() / 'imasdb'

config = {
    'tag': 'data_01',
    'create': {
        'runs_dir':
        None,
        'template':
        str(TEMPLATE_MODEL),
        'template_data': {
            'user': str(IMASDB),
            'db': 'jet',
            'shot': 123,
            'run': 1,
        },
        'operations': [
            {
                'variable': 'major_radius',
                'operator': 'copyto',
                'value': 123.0,
            },
        ],
        'dimensions': [
            {
                'variable': 't_e',
                'operator': 'multiply',
                'values': [0.8, 1.0, 1.2]
            },
        ],
    },
    'system': {
        'name': 'jetto',
        'submit_command': 'true',
    },
}


@pytest.fixture(scope='module')
def tmpworkdir():
    jruns = os.environ.get('JRUNS', '.')

    with tempfile.TemporaryDirectory(dir=jruns) as workdir:
        config['create']['runs_dir'] = workdir
        yield workdir


@pytest.mark.dependency()
def test_create(tmpworkdir):
    ret = create(config, force=True)

    for job, _ in ret.values():
        assert job.in_file.exists()
        job.submit()

    for _, run in ret.values():
        assert run.data_in.exists()


@pytest.mark.dependency(depends=['test_create'])
def test_recreate(tmpworkdir):
    dirname = 'run_0000'

    run_path = Path(tmpworkdir, dirname)

    shutil.rmtree(run_path)

    assert not run_path.exists()

    ret = recreate(config, runs=[Path(dirname)])

    job, run = ret[dirname]

    assert run_path == run.dirname
    assert run_path.exists()
    assert run.data_in.exists()


@pytest.mark.dependency(depends=['test_recreate'])
def test_submit(tmpworkdir):
    for path in Path(tmpworkdir).glob('run_*/duqtools.submit.lock'):
        path.unlink()

    job_queue = submit(config, parent_dir=Path(tmpworkdir))

    assert len(job_queue) == 3

    for job in job_queue:
        assert job.lockfile.exists()


@pytest.mark.dependency(depends=['test_submit'])
def test_resubmit(tmpworkdir):
    path = Path(tmpworkdir, 'run_0000', 'duqtools.submit.lock')
    path.unlink()

    resubmit = (Path(tmpworkdir, 'run_0000'), )

    job_queue = submit(config, resubmit=resubmit, parent_dir=Path(tmpworkdir))

    assert len(job_queue) == 1

    for job in job_queue:
        assert job.lockfile.exists()


@pytest.mark.dependency(depends=['test_recreate'])
def test_submit_array(tmpworkdir):
    submit(config, array=True, parent_dir=Path(tmpworkdir), force=True)

    assert Path('duqtools_slurm_array.sh').exists()


@pytest.mark.dependency(depends=['test_recreate'])
def test_status():
    tracker = get_status(config)
    assert len(tracker.jobs) == 3


def test_example_plot():
    pytest.xfail('`duqtools plot` is not compatible with local imasdb, '
                 'so we no way of testing this currently')

    import subprocess as sp

    from duqtools.ids import imas_mocked
    from duqtools.utils import work_directory
    if imas_mocked:
        pytest.xfail('Imas needed for plotting Imas data')

    cmd = ('duqtools plot -h public/jet/123/1 -v zeff').split()

    with work_directory('.'):
        result = sp.run(cmd)
        assert (result.returncode == 0)
        assert (Path('./chart_rho_tor_norm-zeff.html').exists())
