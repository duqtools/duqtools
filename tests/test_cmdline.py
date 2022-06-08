import os
import subprocess

import pytest


@pytest.mark.dependency()
def test_example_create():
    print(os.getcwd())
    os.chdir('./example')
    result = subprocess.run(['duqtools', 'create', 'config.yaml'])
    assert (result.returncode == 0)
    os.chdir('../')


@pytest.mark.dependency(depends=['test_example_create'])
def test_example_status():
    os.chdir('./example')
    result = subprocess.run(['duqtools', 'status', 'config.yaml'])
    assert (result.returncode == 0)
    os.chdir('../')
