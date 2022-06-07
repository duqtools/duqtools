from pathlib import Path

from duqtools.jetto import JettoSettings, read_jset, write_jset

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


def test_JettoSettings(tmp_path):
    fn = Path(__file__).parent / 'trimmed_jetto.jset'
    jset = JettoSettings.from_file(fn)

    from duqtools.jetto._jset import JINTRAC_CONFIG_VARS

    assert isinstance(jset.metadata, dict)
    assert isinstance(jset.settings, dict)

    test_values = {
        int: 123,
        float: 3.14,
        str: 'quack',
    }

    for var in JINTRAC_CONFIG_VARS:
        var_type = var['type']
        var_name = var['name']
        var_key = var['key']
        value = getattr(jset, var_name)
        assert isinstance(value, var_type)

        test_value = test_values[var_type]
        setattr(jset, var_name, test_value)

        assert jset.settings[var_key] == str(test_value)
