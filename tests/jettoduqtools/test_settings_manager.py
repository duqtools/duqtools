import shutil
from pathlib import Path

import pytest

TEST_DATA = Path.cwd() / 'tests' / 'test_data'


def test_settings_manager(tmp_path):
    pytest.xfail('about to be removed')
    from duqtools.jettoduqtools import JettoSettingsManager
    shutil.copyfile(TEST_DATA / 'template_model' / 'jetto.in',
                    tmp_path / 'jetto.in')
    shutil.copyfile(TEST_DATA / 'template_model' / 'jetto.jset',
                    tmp_path / 'jetto.jset')

    jman = JettoSettingsManager.from_directory(tmp_path)

    assert jman.shot_in != 12345

    jman.shot_in = 12345

    assert jman.handlers['jetto.jset'].settings[
        'SetUpPanel.idsIMASDBShot'] == 12345
    assert jman.handlers['jetto.jset'].settings[
        'AdvancedPanel.catShotID'] == 12345
    assert jman.handlers['jetto.jset'].settings[
        'AdvancedPanel.catShotID_R'] == 12345
    assert jman.handlers['jetto.in'].raw_mapping['inesco']['npulse'] == 12345

    new_configs = tmp_path / 'new_configs'
    new_configs.mkdir()

    jman.to_directory(new_configs)

    assert (new_configs / 'jetto.in').exists()
    assert (new_configs / 'jetto.jset').exists()
