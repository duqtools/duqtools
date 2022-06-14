from duqtools.samplers import latin_hypercube


def test_latin_hypercube():
    i = list('ab')
    j = list('cde')
    k = list('fghi')

    latin_hypercube(i, j, k, n_samples=5)
