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
import saltext.salt_describe.runners.salt_describe_sysctl as salt_describe_sysctl_runner

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"salt.execute": salt_runner.execute},
        "__opts__": salt.config.DEFAULT_MASTER_OPTS.copy(),
    }
    return {
        salt_describe_runner: module_globals,
        salt_describe_sysctl_runner: module_globals,
    }


def test_sysctl():
    sysctl_show = {"minion": {"vm.swappiness": 60, "vm.vfs_cache_pressure": 100}}

    expected_calls = [
        call().write(
            "sysctl-vm.swappiness:\n  sysctl.present:\n  - name: vm.swappiness\n  - value: 60\n"
        ),
        call().write("include:\n- minion.sysctl\n"),
    ]

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=sysctl_show)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=["/srv/salt", "/srv/spm/salt"])},
        ):
            with patch("os.listdir", return_value=["sysctl.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_sysctl_runner.sysctl("minion", ["vm.swappiness"]) is True
                    open_mock.return_value.write.assert_has_calls(expected_calls, any_order=True)


# pylint: enable=line-too-long
