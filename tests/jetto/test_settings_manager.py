import shutil
from pathlib import Path

from duqtools.jetto import JettoSettingsManager

this_path = Path(__file__).parent


def test_settings_manager(tmp_path):
    shutil.copyfile(this_path / 'trimmed_jetto.in', tmp_path / 'jetto.in')
    shutil.copyfile(this_path / 'trimmed_jetto.jset', tmp_path / 'jetto.jset')

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
