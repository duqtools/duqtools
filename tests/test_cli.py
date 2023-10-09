from __future__ import annotations

import pytest
from click.testing import CliRunner
from pytest import TEST_DATA

from duqtools import cli
from duqtools.utils import work_directory


@pytest.fixture(scope='module')
def duqtools_tmpdir(tmpdir_factory):
    return tmpdir_factory.mktemp('duqtools_tmp')


def test_no_command(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli)

    assert ret.exit_code == 0
    assert ret.output.startswith('Usage:')


def test_version(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):

        runner = CliRunner()
        ret = runner.invoke(cli.cli_version)

    assert ret.exit_code == 0


def test_list_variables(duqtools_tmpdir):
    config = TEST_DATA / 'config_list-vars.yaml'
    with work_directory(duqtools_tmpdir):

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


def test_clean(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_clean, [
            '--force',
            '--yes',
        ])

    assert ret.exit_code == 1
    assert ret.output.strip(
    ) == "[Errno 2] No such file or directory: 'duqtools.yaml'"


def test_create(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_create, [
            '--force',
            '--yes',
        ])

    assert ret.exit_code == 1
    assert ret.output.strip(
    ) == "[Errno 2] No such file or directory: 'duqtools.yaml'"


@pytest.mark.skip(reason='Starting the server blocks the rest of the tests.')
def test_dash(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_dash)

    assert ret.exit_code == 0


def test_go(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_go)

    assert ret.exit_code == 1
    assert ret.output.strip(
    ) == "[Errno 2] No such file or directory: 'duqtools.yaml'"


def test_init(tmpdir):
    # must run in a different tmpdir becuase it generated duqtools.yaml
    with work_directory(tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_init, [
            '--force',
            '--yes',
        ])

    assert ret.exit_code == 0
    assert (tmpdir / 'duqtools.yaml').exists()


def test_merge(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_merge, [
            '--force',
            '--yes',
        ])

    assert ret.exit_code == 2
    assert ret.output.splitlines(
    )[-1] == "Error: Missing option '-t' / '--template'."


def test_plot(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_plot)

    assert ret.exit_code == 1
    assert ret.output.strip() == 'No data to show.'


def test_recreate(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_recreate, [
            '--yes',
        ])

    assert ret.exit_code == 1
    assert ret.output.strip(
    ) == "[Errno 2] No such file or directory: 'duqtools.yaml'"


def test_setup(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_setup, [
            '--force',
            '--yes',
        ])

    assert ret.exit_code == 2
    assert ret.output.splitlines()[-1] == (
        "Error: Invalid value for '-t' / '--template': "
        "Path 'duqtools.template.yaml' does not exist.")


def test_status(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_status)

    assert ret.exit_code == 1
    assert ret.output.strip(
    ) == "[Errno 2] No such file or directory: 'duqtools.yaml'"


def test_submit(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_submit, [
            '--force',
            '--yes',
        ])
    assert ret.exit_code == 1
    assert ret.output.strip(
    ) == "[Errno 2] No such file or directory: 'duqtools.yaml'"


def test_sync_prominence(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_sync_prominence, [
            '--force',
            '--yes',
        ])

    assert ret.exit_code == 1
    assert ret.output.strip(
    ) == "[Errno 2] No such file or directory: 'duqtools.yaml'"


def test_yolo(duqtools_tmpdir):
    with work_directory(duqtools_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_yolo)

    assert ret.exit_code == 1
    assert ret.output.strip(
    ) == "[Errno 2] No such file or directory: 'duqtools.yaml'"
