from __future__ import annotations

import os
from collections import defaultdict
from contextlib import contextmanager
from itertools import filterfalse, tee
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Hashable, Iterable

from ._types import PathLike

if TYPE_CHECKING:
    from .ids import ImasHandle


def no_op(*args, **kwargs):
    """Do nothing."""
    pass


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


def read_imas_handles_from_file(inp: PathLike, ) -> dict[str, ImasHandle]:
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
    as_dataframe : bool, optional
        Return imas handles in a dataframe instead.

    Returns
    -------
    Union[dict[str, ImasHandle], 'pd.DataFrame']
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
            has_header = csv.Sniffer().has_header(f.read(1024))
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
        runs = Runs.parse_file(inp)
        handles = {
            str(run.dirname): ImasHandle.parse_obj(run.data_out)
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


def partition(pred: Callable, iterable: Iterable) -> tuple[Iterable, Iterable]:
    """Use a predicate to partition entries into false entries and true
    entries.

    partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9

    From: https://docs.python.org/3/library/itertools.html

    Parameters
    ----------
    pred : Callable
        Filter function called on every entry in the iterable to determine
        whether to put it in the false or true bin
    iterable : Iterable
        List of items to partition

    Returns
    -------
    tuple[Iterable, Iterable]
        Two sequences with false and true entries, respectively.
    """
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)
