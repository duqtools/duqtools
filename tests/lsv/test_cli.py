from __future__ import annotations

import pytest
from click.testing import CliRunner

from duqtools.large_scale_validation import cli
from duqtools.utils import work_directory


@pytest.fixture(scope='module')
def duqduq_tmpdir(tmpdir_factory):
    return tmpdir_factory.mktemp('duqduq_tmp')


def test_no_command(duqduq_tmpdir):
    with work_directory(duqduq_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli)

    assert ret.exit_code == 0
    assert ret.output.startswith('Usage:')


def test_setup(duqduq_tmpdir):
    with work_directory(duqduq_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_setup, [
            '--force',
            '--yes',
        ])

    assert ret.exit_code == 2
    assert ret.output.splitlines()[-1] == (
        "Error: Invalid value for '-i' / '--input': "
        "Path 'data.csv' does not exist.")


def test_create(duqduq_tmpdir):
    with work_directory(duqduq_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_create, [
            '--force',
            '--yes',
        ])

    # No actions to execute.
    assert ret.exit_code == 0


def test_submit(duqduq_tmpdir):
    with work_directory(duqduq_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_submit, [
            '--force',
            '--yes',
        ])

    # No actions to execute.
    assert ret.exit_code == 0


def test_status(duqduq_tmpdir):
    with work_directory(duqduq_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_status, [])

    assert ret.exit_code == 0
    assert ret.output.startswith('Status codes:')


def test_merge(duqduq_tmpdir):
    with work_directory(duqduq_tmpdir):
        runner = CliRunner()
        ret = runner.invoke(cli.cli_merge, [
            '--force',
            '--yes',
        ])

    assert ret.exit_code == 0
    csv = (duqduq_tmpdir / 'merge_data.csv')
    assert csv.exists()
    assert csv.read() == '""\n'
