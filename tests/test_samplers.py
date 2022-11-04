from duqtools.matrix_samplers import (cartesian_product, halton,
                                      latin_hypercube, sobol)


def test_cartesian_product():
    i = 'ab'
    j = 'def'

    ret = cartesian_product(i, j)

    assert ret == [('a', 'd'), ('a', 'e'), ('a', 'f'), ('b', 'd'), ('b', 'e'),
                   ('b', 'f')]


def test_latin_hypercube():
    i = 'ab'
    j = 'cde'
    k = 'fghi'

    ret = latin_hypercube(i, j, k, n_samples=3, seed=123)

    assert ret == [('b', 'e', 'h'), ('b', 'd', 'h'), ('a', 'c', 'f')]


def test_sobol():
    i = 'ab'
    j = 'cde'
    k = 'fghi'

    ret = sobol(i, j, k, n_samples=4, seed=123)

    assert ret == [('b', 'd', 'g'), ('a', 'c', 'i'), ('a', 'e', 'f'),
                   ('b', 'c', 'h')]


def test_halton():
    i = 'ab'
    j = 'cde'
    k = 'fghi'

    ret = halton(i, j, k, n_samples=4, seed=123)

    import sys
    vi = sys.version_info
    if vi.major <= 3 and vi.minor <= 7:
        assert ret == [('a', 'c', 'i'), ('b', 'e', 'f'), ('a', 'd', 'h'),
                       ('b', 'c', 'h')]
    else:
        assert ret == [('a', 'c', 'i'), ('b', 'e', 'f'), ('a', 'd', 'h'),
                       ('b', 'c', 'i')]
