from duqtools.io import patch_namelist, read_namelist, write_namelist

nml = {'nlist1': {'a': 123, 'b': 456}, 'nlist2': {'c': [1, 2, 3], 'd': None}}


def test_namelist_io(tmp_path):
    path = tmp_path / 'jetto.in'

    write_namelist(path, nml)
    nml2 = read_namelist(path)

    assert nml == nml2


def test_patch_namelist(tmp_path):
    path = tmp_path / 'jetto.in'
    out = tmp_path / 'patched_jetto.in'

    patch = {'nlist1': {'a': 321}, 'nlist3': {'e': 'asdf'}}

    write_namelist(path, nml)
    patched = patch_namelist(path, patch, out)

    assert out.exists()
    expected_nlist1 = {**nml['nlist1'], **patch['nlist1']}
    assert patched['nlist1'] == expected_nlist1
    assert patched['nlist2'] == nml['nlist2']
    assert patched['nlist3'] == patch['nlist3']
