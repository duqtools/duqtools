def test_imas():
    from unittest.mock import MagicMock as Mock

    import pytest

    from duqtools.ids._imas import imas, imasdef

    pytest.xfail(
        'this is only to test imas imports, expected to fail on non-imas systems'
    )
    assert type(imas) is not Mock
    assert type(imasdef) is not Mock
