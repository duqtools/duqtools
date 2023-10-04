from __future__ import annotations

import itertools
from typing import Any, Optional

from scipy.stats import qmc


def cartesian_product(*iterables, **kwargs) -> list[Any]:
    """Return cartesian product of input iterables.

    Uses `itertools.product`

    Parameters
    ----------
    *iterables
        Input iterables.

    Returns
    -------
    list[Any]
        List of product of input arguments.
    """
    return list(itertools.product(*iterables))


def _sampler(func, *iterables, n_samples: int, **kwargs) -> list[Any]:
    """Generic sampler."""
    bounds = tuple(len(iterable) for iterable in iterables)

    sampler = func(d=len(iterables), **kwargs)
    indices = sampler.integers(l_bounds=bounds, n=n_samples)

    samples = []
    for row in indices:
        samples.append(tuple(arg[col] for col, arg in zip(row, iterables)))

    return samples


def latin_hypercube(*iterables,
                    n_samples: int,
                    seed: Optional[int] = None,
                    **kwargs) -> list[Any]:
    """Sample input iterables using Latin hypercube sampling (LHS).

    Uses `scipy.stats.qmc.LatinHyperCube`.

    Parameters
    ----------
    *iterables
        Iterables to sample from.
    n_samples : int
        Number of samples to return.
    seed : int, optional
        Seed to use for the randomizer

    Returns
    -------
    samples : list[Any]
        List of sampled input arguments.
    """
    return _sampler(qmc.LatinHypercube,
                    *iterables,
                    n_samples=n_samples,
                    seed=seed)


def sobol(*iterables,
          n_samples: int,
          seed: Optional[int] = None,
          **kwargs) -> list[Any]:
    """Sample input iterables using the Sobol sampling method for generating
    low discrepancy sequences.

    Uses `scipy.stats.qmc.Sobol`.

    Parameters
    ----------
    *iterables
        Iterables to sample from.
    n_samples : int
        Number of samples to return. Note that Sobol sequences lose their
        balance  properties if one uses a sample size that is not a power
        of two.
    seed : int, optional
        Seed to use for the randomizer

    Returns
    -------
    samples : list[Any]
        List of sampled input arguments.
    """
    return _sampler(qmc.Sobol, *iterables, n_samples=n_samples, seed=seed)


def halton(*iterables,
           n_samples: int,
           seed: Optional[int] = None,
           **kwargs) -> list[Any]:
    """Sample input iterables using the Halton sampling method.

    Uses `scipy.stats.qmc.Halton`.

    Parameters
    ----------
    *iterables
        Iterables to sample from.
    n_samples : int
        Number of samples to return.
    seed : int, optional
        Seed to use for the randomizer

    Returns
    -------
    samples : list[Any]
        List of sampled input arguments.
    """
    return _sampler(qmc.Halton, *iterables, n_samples=n_samples, seed=seed)


_SAMPLERS = {
    'latin-hypercube': latin_hypercube,
    'halton': halton,
    'sobol': sobol,
    'low-discrepancy-sequence': sobol,
    'cartesian-product': cartesian_product,
}


def get_matrix_sampler(name: str):
    """Get sampler.

    Parameters
    ----------
    name : str
        Name of the sampler.

    Returns
    -------
    Callable
        Sampling function.
    """
    return _SAMPLERS[name]
