import numpy as np
from scipy.stats import qmc


def latin_hypercube(*args, n_samples: int):
    """Sample from *args using Latin hypercube sampling (LHS).

    Uses `scip.stats.qmc.LatinHyperCube`.

    Parameters
    ----------
    *args
        Sequences to sample from.
    n_samples : int
        Number of samples to return.

    Returns
    -------
    samples : list[Any]
        List of sampled input arguments.
    """
    bounds = tuple(len(seq) for seq in args)

    sampler = qmc.LatinHypercube(d=len(args))
    unit_samples = sampler.random(n_samples)

    indices = np.floor(unit_samples * np.array(bounds)).astype(int)

    samples = []
    for row in indices:
        samples.append(tuple(arg[col] for col, arg in zip(row, args)))

    return samples
