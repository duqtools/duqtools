from __future__ import annotations

import os
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Callable, Hashable, Iterable

from pydantic_yaml import parse_yaml_raw_as

if TYPE_CHECKING:
    from ._types import PathLike
    from .ids import ImasHandle


def formatter(s):
    """Dedent and remove newlines."""
    s = dedent(s)
    return s.replace('\n', ' ').strip()


@contextmanager
def work_directory(path: PathLike):
    """Changes working directory and returns to previous on exit.

    Parameters
    ----------
    path : PathLike
        Temporarily change to this directory.
    """
    prev_cwd = Path.cwd().resolve()
    try:
        os.chdir(path)
        yield
    finally:  # In any case, no matter what happens, go back eventually
        os.chdir(prev_cwd)


def read_imas_handles_from_file(inp: PathLike) -> dict[str, ImasHandle]:
    """Read a collection of imas paths from a file.

    Input can be a `Runs.yaml` file `data.csv` file.

    The CSV file must have contain at least 5 columns, including: `user`,
    `db`, `shot`, and `run`. The first column is used as the index.
    The index can be any string or number, as long as it uniquely
    identifies the row.

    Parameters
    ----------
    inp : PathLike
        Name of the file to read.

    Returns
    -------
    dict[str, ImasHandle]
        Returns a dict with the Imas handles.

    Raises
    ------
    ValueError
        When the file cannot be opened.
    """
    import csv

    from .ids import ImasHandle
    from .models import Runs

    inp = Path(inp)

    if inp.suffix == '.csv':
        handles = {}
        with open(inp) as f:
            has_header = csv.Sniffer().has_header(''.join(f.readlines(3)))
            f.seek(0)

            if not has_header:
                raise IOError(
                    f'`{inp}` does not have a header. Expecting at least'
                    '`user`,`db`,`shot`,`run`.')

            reader = csv.DictReader(f)

            index_col = reader.fieldnames[0]  # type: ignore

            for row in reader:
                index = row.pop(index_col)
                handles[index] = ImasHandle(**row)

    elif inp.name == 'runs.yaml':
        with open(inp) as f:
            runs = parse_yaml_raw_as(Runs, f)
        handles = {
            str(run.dirname): ImasHandle.model_validate(run.data_out,
                                                        from_attributes=True)
            for run in runs
        }

    else:
        raise ValueError(f'Cannot open file: {inp}')

    return handles


def groupby(iterable: Iterable,
            keyfunc: Callable) -> dict[Hashable, list[Any]]:
    """Group iterable by key function. The items are grouped by the value that
    is returned by the `keyfunc`

    Parameters
    ----------
    iterable : list, tuple or iterable
        List of items to group
    keyfunc : callable
        Used to determine the group of each item. These become the keys
        of the returned dictionary

    Returns
    -------
    grouped : dict
        Returns a dictionary with the grouped values.
    """
    grouped = defaultdict(list)
    for item in iterable:
        key = keyfunc(item)
        grouped[key].append(item)

    return grouped
