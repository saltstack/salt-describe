# pylint: disable=line-too-long
import logging
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
import salt.config  # pylint: disable=import-error
import salt.runners.salt as salt_runner  # pylint: disable=import-error
import saltext.salt_describe.runners.salt_describe as salt_describe_runner
import saltext.salt_describe.runners.salt_describe_timezone as salt_describe_timezone_runner
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
        salt_describe_timezone_runner: module_globals,
    }


def test_timezone(tmp_path):
    """
    test describe.host
    """
    timezone_list = {"poc-minion": "America/Los_Angeles"}

    expected_content = {"America/Los_Angeles": {"timezone.system": []}}
    expected_sls_write = yaml.dump(expected_content)

    expected_include_write = yaml.dump({"include": ["poc-minion.timezone"]})
    expected_calls = [
        call().write(expected_sls_write),
        call().write(expected_include_write),
    ]

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=timezone_list)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[tmp_path])},
        ):
            assert salt_describe_timezone_runner.timezone("minion") is True
            with patch("os.listdir", return_value=["timezone.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_timezone_runner.timezone("minion") is True
                    open_mock.assert_has_calls(expected_calls, any_order=True)


# pylint: enable=line-too-long
