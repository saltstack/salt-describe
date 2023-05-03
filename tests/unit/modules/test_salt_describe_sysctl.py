# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging
from pathlib import PosixPath
from pathlib import WindowsPath
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
import saltext.salt_describe.modules.salt_describe_sysctl as salt_describe_sysctl_module
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_sysctl_module: {
            "__salt__": {"config.get": MagicMock(return_value="minion")},
            "__opts__": {},
        },
    }


def test_sysctl():
    sysctl_show = {"vm.swappiness": 60, "vm.vfs_cache_pressure": 100}

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
        salt_describe_sysctl_module.__salt__, {"sysctl.show": MagicMock(return_value=sysctl_show)}
    ):
        with patch.object(salt_describe_sysctl_module, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_sysctl_module.sysctl(
                ["vm.swappiness"]
            )
            generate_mock.assert_called_with(
                {}, "minion", sysctl_sls, sls_name="sysctl", config_system="salt"
            )


def test_sysctl_permission_denied(caplog, minion_opts, perm_denied_error_log):
    sysctl_show = {"vm.swappiness": 60, "vm.vfs_cache_pressure": 100}

    with patch.dict(
        salt_describe_sysctl_module.__salt__, {"sysctl.show": MagicMock(return_value=sysctl_show)}
    ):
        with patch.dict(salt_describe_sysctl_module.__opts__, minion_opts):
            with patch.object(PosixPath, "mkdir", side_effect=PermissionError), patch.object(
                WindowsPath, "mkdir", side_effect=PermissionError
            ):
                with caplog.at_level(logging.WARNING):
                    ret = salt_describe_sysctl_module.sysctl(["vm.swappiness"])
                    assert not ret
                    assert perm_denied_error_log in caplog.text
