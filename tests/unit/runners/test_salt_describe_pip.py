# pylint: disable=line-too-long
import logging
import pathlib
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
import salt.config  # pylint: disable=import-error
import salt.runners.salt as salt_runner  # pylint: disable=import-error
import saltext.salt_describe.runners.salt_describe as salt_describe_runner
import saltext.salt_describe.runners.salt_describe_pip as salt_describe_pip_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"salt.execute": salt_runner.execute},
        "__opts__": salt.config.DEFAULT_MASTER_OPTS.copy(),
    }
    return {
        salt_describe_runner: module_globals,
        salt_describe_pip_runner: module_globals,
    }


def test_pip(tmp_path):
    pip_list = {
        "minion": [
            "requests==0.1.2",
            "salt==3004.1",
            "argcomplete==2.3.4-5",
        ],
    }

    expected_sls_write = yaml.dump(
        {
            "installed_pip_libraries": {"pip.installed": [{"pkgs": pip_list["minion"]}]},
        }
    )
    expected_include_write = yaml.dump({"include": ["minion.pip"]})
    expected_calls = [
        call().write(expected_sls_write),
        call().write(expected_include_write),
    ]
    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=pip_list)}
    ):
        tmp_state_root = pathlib.Path(tmp_path, "srv", "salt")
        tmp_state_root.mkdir(parents=True, exist_ok=True)
        unused_dir = pathlib.Path(tmp_path, "srv", "spm", "salt")
        unused_dir.mkdir(parents=True, exist_ok=True)
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[str(tmp_state_root), str(unused_dir)])},
        ):
            with patch("os.listdir", return_value=["pip.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_pip_runner.pip("minion") is True
                    open_mock.assert_has_calls(expected_calls, any_order=True)


# pylint: enable=line-too-long
