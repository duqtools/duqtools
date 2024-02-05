from __future__ import annotations

from inspect import signature
from pathlib import Path
from typing import Any, Callable, List, Optional

from .ids import ImasHandle
from .models import Locations, Run


def _duqmap(function: Callable[[Any], Any],
            convert: Callable[[Run], Any],
            runs: Optional[List[Any]] = None) -> List[Any]:
    if not runs:
        runs = Locations().runs

    ret = []
    for run in runs:
        if isinstance(run, Run):
            pass
        elif isinstance(run, Path):
            run = Run.from_path(run)
        else:
            raise NotImplementedError(
                f'Dont know how to convert: {type(run)} {run}, to Run')
        ret.append(function(convert(run)))
    return ret


def duqmap_run(function: Callable[[Run], Any], **kwargs) -> List[Any]:
    return _duqmap(function, lambda x: x, **kwargs)  # Identity


def duqmap_imas(function: Callable[[ImasHandle], Any], **kwargs) -> List[Any]:

    def to_imas_handle(run):
        return run.to_imas_handle()

    return _duqmap(function, to_imas_handle, **kwargs)


def duqmap(function: Callable[[Run | ImasHandle], Any],
           *,
           runs: Optional[List[Run | Path]] = None,
           **kwargs) -> List[Any]:
    """Duqmap is a mapping function which can be used to map a user defined
    function `function` over either the runs created by duqtools, or the runs
    specified by the user in `runs`.

    An important gotcha is that when `Paths` are used to define the runs, duqtools
    does not know how to associate the corresponding ImasHandles, as that information
    is not available.  So when using it in this way, it is not possible to provide a
    function which takes an `ImasHandle` as input.

    Parameters
    ----------
    function : Callable[[Run | ImasHandle], Any]
        function which is called for each run, specified either by `runs`, or implicitly
        by any available `runs.yaml`
    runs : Optional[List[Run | Path]]
        A list of runs over which to operate the function
    kwargs :
        optional arguments that need to be passed to each `function` that you provide

    Returns
    -------
    List[Any]:
        A list of anything that your function returns
    """
    try:
        # Gets the type of the first argument to the function, if it exists
        argument = next(iter(signature(function).parameters.items()))[1]
    except Exception:
        raise NotImplementedError(
            f'Dont know how to map: {function}, which has no arguments')

    argument_type = argument.annotation

    if argument_type in [Run, 'Run']:
        map_fun: Callable[[Any], Any] = duqmap_run
    elif argument_type in [ImasHandle, 'ImasHandle']:
        map_fun = duqmap_imas
    else:
        raise NotImplementedError('Dont know how to map function signature:'
                                  f' {function.__name__}{signature(function)}')

    return map_fun(function, runs=runs, **kwargs)  # type: ignore
