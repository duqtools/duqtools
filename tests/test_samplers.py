from duqtools.samplers import cartesian_product, latin_hypercube


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
