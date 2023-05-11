import os
import tempfile
from pathlib import Path

from duqtools.api import create

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


def test_create():
    jruns = os.environ['JRUNS']

    with tempfile.TemporaryDirectory(dir=jruns) as workdir:
        config['create']['runs_dir'] = workdir

        jobs, runs = create(config, force=True)

        for job in jobs:
            assert job.in_file.exists()
            job.submit()

        for run in runs:
            assert run.data_in.exists()
