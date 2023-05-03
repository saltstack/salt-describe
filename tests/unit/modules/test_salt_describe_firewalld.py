# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging
from pathlib import PosixPath
from pathlib import WindowsPath
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.modules.salt_describe_firewalld as salt_describe_firewalld_module
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_firewalld_module: {
            "__salt__": {"config.get": MagicMock(return_value="minion")},
            "__opts__": {},
        },
    }


@pytest.fixture
def firewalld_ret():
    yield {
        "public": {
            "target": ["default"],
            "icmp-block-inversion": ["no"],
            "interfaces": [""],
            "sources": [""],
            "services": ["dhcpv6-client ssh"],
            "ports": [""],
            "protocols": [""],
            "forward": ["yes"],
            "masquerade": ["no"],
            "forward-ports": [""],
            "source-ports": [""],
            "icmp-blocks": [""],
            "rich rules": [""],
        }
    }


def test_firewalld(firewalld_ret):
    """
    test describe.firewalld
    """
    firewalld_sls_contents = {
        "add_firewalld_rule_0": {
            "firewalld.present": [{"name": "public"}, {"services": ["dhcpv6-client", "ssh"]}]
        }
    }
    firewalld_sls = yaml.dump(firewalld_sls_contents)

    with patch.dict(
        salt_describe_firewalld_module.__salt__,
        {"firewalld.list_all": MagicMock(return_value=firewalld_ret)},
    ):
        with patch.object(salt_describe_firewalld_module, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_firewalld_module.firewalld()
            generate_mock.assert_called_with(
                {}, "minion", firewalld_sls, sls_name="firewalld", config_system="salt"
            )


def test_firewalld_unavailable():
    """
    test describe.firewalld
    """
    firewalld_ret = "'firewalld' __virtual__ returned False: The firewalld execution module cannot be loaded: the firewall-cmd binary is not in the path."

    with patch.dict(
        salt_describe_firewalld_module.__salt__,
        {"firewalld.list_all": MagicMock(return_value=firewalld_ret)},
    ):
        with patch.object(salt_describe_firewalld_module, "generate_files") as generate_mock:
            ret = salt_describe_firewalld_module.firewalld()


def test_firewalld_permissioned_denied(minion_opts, caplog, firewalld_ret, perm_denied_error_log):
    with patch.dict(
        salt_describe_firewalld_module.__salt__,
        {"firewalld.list_all": MagicMock(return_value=firewalld_ret)},
    ):
        with patch.dict(salt_describe_firewalld_module.__opts__, minion_opts):
            with patch.object(PosixPath, "mkdir", side_effect=PermissionError), patch.object(
                WindowsPath, "mkdir", side_effect=PermissionError
            ):
                with caplog.at_level(logging.WARNING):
                    ret = salt_describe_firewalld_module.firewalld()
                    assert not ret
                    assert perm_denied_error_log in caplog.text
