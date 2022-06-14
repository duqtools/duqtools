import itertools

import numpy as np
from scipy.stats import qmc


def cartesian_product(*iterables):
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


def latin_hypercube(*iterables, n_samples: int, **kwargs):
    """Sample input iterables using Latin hypercube sampling (LHS).

    Uses `scipy.stats.qmc.LatinHyperCube`.

    Parameters
    ----------
    *iterables
        Iterables to sample from.
    n_samples : int
        Number of samples to return.
    **kwargs
        These keyword arguments are passed to `scipy.stats.qmc.LatinHypercube`

    Returns
    -------
    samples : list[Any]
        List of sampled input arguments.
    """
    bounds = tuple(len(iterable) for iterable in iterables)

    sampler = qmc.LatinHypercube(d=len(iterables), **kwargs)
    unit_samples = sampler.random(n_samples)

    indices = np.floor(unit_samples * np.array(bounds)).astype(int)

    samples = []
    for row in indices:
        samples.append(tuple(arg[col] for col, arg in zip(row, iterables)))

    return samples
