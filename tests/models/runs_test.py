from __future__ import annotations

from pathlib import Path

from duqtools.api import ImasHandle
from duqtools.models import Run, Runs


def test_run():
    run = Run(dirname=Path('a/b'),
              data_out={
                  'db': 'test',
                  'user': 'test',
                  'run': 0,
                  'shot': 0
              })
    assert str(run.shortname) == 'b'

    h = run.to_imas_handle()
    assert isinstance(h, ImasHandle)


def test_runs():
    runs = Runs((
        Run(dirname=Path('a')),
        Run(dirname=Path('b')),
        Run(dirname=Path('c')),
    ))
    assert len(runs) == 3
    assert isinstance(runs[0], Run)
    assert [run for run in runs]
