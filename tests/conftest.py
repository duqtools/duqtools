from __future__ import annotations

from pathlib import Path

import pytest


def pytest_configure():
    pytest.TEST_DATA = Path(__file__).parent / 'test_data'
