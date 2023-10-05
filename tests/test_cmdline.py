from __future__ import annotations

from click.testing import CliRunner
from pytest import TEST_DATA

from duqtools import cli


def test_list_variables():
    config = TEST_DATA / 'config_list-vars.yaml'

    runner = CliRunner()
    ret = runner.invoke(cli.cli_list_variables, [
        '-c',
        f'{config}',
    ])

    assert ret.exit_code == 0

    out = ret.output
    assert 'IDS-variable' in out
    assert 'jetto-variable' in out
    assert '*my_extra_var' in out
    assert 'rho_tor_norm' in out
