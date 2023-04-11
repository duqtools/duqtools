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
    try:
        # Gets the type of the first argument to the function, if it exists
        argument = next(iter(signature(function).parameters.items()))[1]
    except Exception:
        raise NotImplementedError(
            f'Dont know how to map: {function}, which has no arguments')

    argument_type = argument.annotation

    if issubclass(argument_type, Run):
        map_fun: Callable[[Any], Any] = duqmap_run
    elif issubclass(argument_type, ImasHandle):
        map_fun = duqmap_imas
    else:
        raise NotImplementedError('Dont know how to map function signature:'
                                  f' {function.__name__}{signature(function)}')

    return map_fun(function, runs=runs, **kwargs)  # type: ignore
