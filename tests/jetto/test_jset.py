from duqtools.jetto import read_jset, write_jset

JSET = {
    'section 1': {
        'a': '123',
        'b': '456'
    },
    'section 2': {
        'c[0]': '1',
        'c[1]': '2',
        'c[2]': '3',
        'd': ''
    },
}


def test_jset_io(tmp_path):
    path = tmp_path / 'jetto.jset'

    write_jset(path, JSET)
    jset2 = read_jset(path)

    assert JSET == jset2
