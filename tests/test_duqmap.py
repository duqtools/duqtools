from pathlib import Path

import pytest

from duqtools.api import ImasHandle, Run, duqmap


def fun_run(run: Run):
    return run.dirname
    assert (isinstance(run, Run))


def fun_handle(handle: ImasHandle):
    assert (isinstance(handle, ImasHandle))


def fun_str(x: str):
    assert (isinstance(x, str))


def fun_none():
    pytest.fail("This function shouldn't be reached")


def test_duqmap():
    with pytest.raises(NotImplementedError):
        duqmap(fun_none)
    with pytest.raises(NotImplementedError):
        duqmap(fun_str)
    with pytest.raises(NotImplementedError):
        duqmap(fun_handle, runs=[Path('xxx')])

    result = duqmap(fun_run, runs=[Path('xxx')])

    assert (result == [Path('xxx').resolve()])
