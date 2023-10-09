from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from duqtools import cli
from duqtools.utils import work_directory

imas = pytest.importorskip('imas',
                           reason='No way of testing this without IMAS')

CONTAINERIZED_RUNS_DIR = os.environ['CONTAINERIZED_RUNS_DIR']
IMASDB = Path(CONTAINERIZED_RUNS_DIR).resolve() / 'imasdb'

CONFIG = {
    'tag': 'data_01',
    'create': {
        'runs_dir':
        None,
        'template_data': {
            'user': str(IMASDB),
            'db': 'jet',
            'shot': 123,
            'run': 1,
        },
        'operations': [
            {
                'variable': 't_e',
                'operator': 'multiply',
                'value': 0,
            },
        ],
    },
    'system': {
        'name': 'nosystem',
    },
}


@pytest.fixture(scope='module')
def tmpworkdir():
    jruns = os.environ.get('JRUNS', '.')

    with tempfile.TemporaryDirectory(dir=jruns) as workdir:
        CONFIG['create']['runs_dir'] = str(Path(workdir).resolve())
        with open(Path(workdir) / 'duqtools.yaml', 'w') as f:
            yaml.dump(CONFIG, f)
        yield workdir


@pytest.mark.dependency()
def test_create(tmpworkdir):
    with work_directory(tmpworkdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_create, [
            '--force',
            '--yes',
        ])

    assert ret.exit_code == 0

    outdir = Path(tmpworkdir)
    for p in 'duqtools.log', 'runs.yaml', 'data.csv', 'run_0000':
        assert (outdir / p).exists()

    for fn in 'ids_1230001.characteristics', 'ids_1230001.datafile', 'ids_1230001.tree':
        assert Path(outdir, 'run_0000', 'imasdb', 'jet', '3', '0', fn).exists()


@pytest.mark.dependency()
def test_merge(tmpworkdir):
    tmpworkdir = Path(tmpworkdir).absolute()
    imasdbdir = Path(tmpworkdir, 'run_0000', 'imasdb')

    with work_directory(tmpworkdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_merge, [
            '--force',
            '--yes',
            *('--template', f'{imasdbdir}/jet/123/1'),
            *('--handle', f'{imasdbdir}/jet/123/1'),
            *('--out', f'{imasdbdir}/jet/123/1001'),
            *('--variable', 't_e'),
        ])

    assert ret.exit_code == 0

    for fn in 'ids_1231001.characteristics', 'ids_1231001.datafile', 'ids_1231001.tree':
        assert Path(imasdbdir, 'jet', '3', '0', fn).exists()
