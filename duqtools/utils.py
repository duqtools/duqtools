import os
from contextlib import contextmanager
from pathlib import Path

from ._types import PathLike


def dry_run_toggle(func):

    def wrapper(*args, **kwargs):
        from .config import cfg
        if not cfg.dry_run:
            return func(*args, **kwargs)

    return wrapper


@contextmanager
def work_directory(path: PathLike):
    """Changes working directory and returns to previous on exit.

    Parameters
    ----------
    path : PathLike
        Temporarily change to this directory.
    """
    prev_cwd = Path.cwd()
    os.chdir(path)
    yield
    os.chdir(prev_cwd)
