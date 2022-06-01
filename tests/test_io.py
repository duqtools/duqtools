from duqtools.io import read_jetto_in, write_jetto_in


def test_jetto_in_io(tmp_path):
    nml = {
        'nlist1': {
            'a': 123,
            'b': 456
        },
        'nlist2': {
            'c': [1, 2, 3],
            'd': None
        }
    }

    jetto_in = tmp_path / 'jetto.in'

    write_jetto_in(jetto_in, nml)
    nml2 = read_jetto_in(jetto_in)

    assert nml == nml2
