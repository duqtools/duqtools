import subprocess as sp

import click
from pytest import TEST_DATA


def test_list_variables():
    config = TEST_DATA / 'config_list-vars.yaml'

    cmd = (f'duqtools list-variables -c {config}').split()

    result = sp.run(cmd, capture_output=True)
    assert (result.returncode == 0)

    out = click.unstyle(result.stdout.decode())
    err = click.unstyle(result.stderr.decode())

    assert err == ''
    assert 'IDS-variable' in out
    assert 'jetto-variable' in out
    assert '*my_extra_var' in out
    assert 'rho_tor_norm' in out
