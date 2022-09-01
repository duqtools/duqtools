from pathlib import Path

from duqtools.jettoduqtools._jetto_in import JettoIn
from duqtools.jettoduqtools._namelist import read_namelist, write_namelist

JETTOIN = {
    'section1': {
        'a': 'text',
        'b': 'more text'
    },
    'section2': {
        'c': 1,
        'd': '1',
        'e': 123.123,
        'f': [1, 2, 3],
    },
}


def test_jetto_in_io(tmp_path):
    path = tmp_path / 'jetto.in'

    header = ['this\n', 'is\n', 'a\n', 'header\n']

    write_namelist(path, namelist=JETTOIN, header=header)
    header2, jin2 = read_namelist(path, header_rows=len(header))

    assert isinstance(jin2, dict)
    assert JETTOIN == jin2


def test_jetto_in(tmp_path):
    fn = Path(__file__).parent / 'trimmed_jetto.in'
    jin = JettoIn.from_file(fn)

    assert isinstance(jin.raw_mapping, dict)
    assert isinstance(jin.header, list)

    section = 'nlist1'
    field = 'BCINTRHON'
    value = 123.123

    jin.set(section=section, field=field, value=value)
    assert jin.get(section=section, field=field) == value
