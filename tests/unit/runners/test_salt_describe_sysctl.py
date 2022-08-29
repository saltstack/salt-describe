import logging
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
import saltext.salt_describe.runners.salt_describe_sysctl as salt_describe_sysctl_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_sysctl_runner: {
            "__salt__": {"salt.execute": MagicMock()},
            "__opts__": {},
        },
    }


def test_sysctl():
    sysctl_show = {"minion": {"vm.swappiness": 60, "vm.vfs_cache_pressure": 100}}

    sysctl_sls_contents = {
        "sysctl-vm.swappiness": {
            "sysctl.present": [
                {"name": "vm.swappiness"},
                {"value": 60},
            ],
        },
    }
    sysctl_sls = yaml.dump(sysctl_sls_contents)

    with patch.dict(
        salt_describe_sysctl_runner.__salt__, {"salt.execute": MagicMock(return_value=sysctl_show)}
    ):
        with patch.object(salt_describe_sysctl_runner, "generate_sls") as generate_mock:
            assert salt_describe_sysctl_runner.sysctl("minion", ["vm.swappiness"]) is True
            generate_mock.assert_called_with({}, "minion", sysctl_sls, sls_name="sysctl")
