def test_imas():
    from unittest.mock import MagicMock as Mock

    import pytest

    from duqtools.ids._imas import imas, imasdef

    if (type(imas) is not Mock) and \
       (type(imasdef) is not Mock):
        # Great, all passed
        return

    pytest.xfail(
        'this is only to test imas imports, expected to fail on non-imas systems'
    )
