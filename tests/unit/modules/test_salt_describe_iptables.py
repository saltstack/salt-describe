# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging
from pathlib import PosixPath
from pathlib import WindowsPath
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.modules.salt_describe_iptables as salt_describe_iptables_module
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_iptables_module: {
            "__salt__": {"config.get": MagicMock(return_value="minion")},
            "__opts__": {},
        },
    }


def test_iptables(tmp_path):
    """
    test describe.iptables
    """
    iptables_ret = {
        "filter": {
            "INPUT": {
                "policy": "ACCEPT",
                "packet count": "319",
                "byte count": "57738",
                "rules": [
                    {"source": ["203.0.113.51/32"], "jump": ["DROP"]},
                    {
                        "protocol": ["tcp"],
                        "jump": ["ACCEPT"],
                        "in-interface": ["eth0"],
                        "match": ["tcp"],
                        "destination_port": ["22"],
                    },
                ],
                "rules_comment": {},
            },
            "FORWARD": {
                "policy": "ACCEPT",
                "packet count": "0",
                "byte count": "0",
                "rules": [],
                "rules_comment": {},
            },
            "OUTPUT": {
                "policy": "ACCEPT",
                "packet count": "331",
                "byte count": "33780",
                "rules": [],
                "rules_comment": {},
            },
        }
    }

    iptables_sls_contents = {
        "add_iptables_rule_0": {
            "iptables.append": [
                {"chain": "INPUT"},
                {"table": "filter"},
                {"source": "203.0.113.51/32"},
                {"jump": "DROP"},
            ]
        },
        "add_iptables_rule_1": {
            "iptables.append": [
                {"chain": "INPUT"},
                {"table": "filter"},
                {"protocol": "tcp"},
                {"jump": "ACCEPT"},
                {"in-interface": "eth0"},
                {"match": "tcp"},
                {"destination-port": "22"},
            ]
        },
    }
    iptables_sls = yaml.dump(iptables_sls_contents)

    with patch.dict(
        salt_describe_iptables_module.__salt__,
        {"iptables.get_rules": MagicMock(return_value=iptables_ret)},
    ):
        with patch.object(salt_describe_iptables_module, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_iptables_module.iptables()
            generate_mock.assert_called_with(
                {}, "minion", iptables_sls, sls_name="iptables", config_system="salt"
            )


def test_iptables_permission_denied(tmp_path, caplog, minion_opts, perm_denied_error_log):
    """
    test describe.iptables
    """
    iptables_ret = {
        "filter": {
            "INPUT": {
                "policy": "ACCEPT",
                "packet count": "319",
                "byte count": "57738",
                "rules": [
                    {"source": ["203.0.113.51/32"], "jump": ["DROP"]},
                    {
                        "protocol": ["tcp"],
                        "jump": ["ACCEPT"],
                        "in-interface": ["eth0"],
                        "match": ["tcp"],
                        "destination_port": ["22"],
                    },
                ],
                "rules_comment": {},
            },
            "FORWARD": {
                "policy": "ACCEPT",
                "packet count": "0",
                "byte count": "0",
                "rules": [],
                "rules_comment": {},
            },
            "OUTPUT": {
                "policy": "ACCEPT",
                "packet count": "331",
                "byte count": "33780",
                "rules": [],
                "rules_comment": {},
            },
        }
    }

    with patch.dict(
        salt_describe_iptables_module.__salt__,
        {"iptables.get_rules": MagicMock(return_value=iptables_ret)},
    ):
        with patch.dict(salt_describe_iptables_module.__opts__, minion_opts):
            with patch.object(PosixPath, "mkdir", side_effect=PermissionError), patch.object(
                WindowsPath, "mkdir", side_effect=PermissionError
            ):
                with caplog.at_level(logging.WARNING):
                    ret = salt_describe_iptables_module.iptables()
                    assert not ret
                    assert perm_denied_error_log in caplog.text
