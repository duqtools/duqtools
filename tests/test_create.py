import os
import shutil
import tempfile
from pathlib import Path

import pytest

from duqtools.api import create, recreate

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
    'system': 'jetto',
    'submit': {
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
    jobs, runs = create(config, force=True)

    for job in jobs:
        assert job.in_file.exists()
        job.submit()

    for run in runs:
        assert run.data_in.exists()


@pytest.mark.dependency(depends=['test_create'])
def test_recreate(tmpworkdir):
    dirname = 'run_0000'

    run_path = Path(tmpworkdir, dirname)

    shutil.rmtree(run_path)

    assert not run_path.exists()

    job, run = recreate(config, runs=[Path(dirname)])

    # assert len(runs) == 1
    # assert len(jobs) == 1
    assert run_path.exists()
    assert run.data_in.exists()
