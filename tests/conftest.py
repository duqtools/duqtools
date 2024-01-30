from __future__ import annotations

import os
from pathlib import Path

import pytest


def pytest_configure():
    pytest.TEST_DATA = Path(__file__).parent / 'test_data'

    os.environ['JETTO_LOOKUP'] = str(pytest.TEST_DATA / 'jetto_lookup.json')
