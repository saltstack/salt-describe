from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.utils.init as describe_util
import yaml


@pytest.mark.parametrize(
    "config_system",
    [
        "salt",
    ],
)
def test_generate_files(tmp_path, config_system):
    state_contents = {
        "salt://testfile": {
            "file.managed": {
                "source": "salt://minion/files/testfile",
            },
        },
    }
    state = yaml.dump(state_contents)
    assert describe_util.generate_files(
        {"file_roots": {"base": [tmp_path / "file_root"]}},
        "minion",
        state,
        sls_name="file",
        config_system=config_system,
    )


@pytest.mark.parametrize(
    "config_system",
    [
        "salt",
    ],
)
def test_get_minion_state_file_root(tmp_path, config_system):
    assert describe_util.get_minion_state_file_root(
        {"file_roots": {"base": [tmp_path / "file_root"]}}, "minion", config_system=config_system
    )
