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
import saltext.salt_describe.runners.salt_describe_iptables as salt_describe_iptables_runner
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
        salt_describe_iptables_runner: module_globals,
    }


def test_iptables(tmp_path):
    """
    test describe.iptables
    """
    iptables_ret = {
        "poc-minion": {
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
    }

    expected_content = {
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

    expected_sls_write = yaml.dump(expected_content)
    expected_include_write = yaml.dump({"include": ["poc-minion.iptables"]})
    expected_calls = [
        call().write(expected_sls_write),
        call().write(expected_include_write),
    ]

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=iptables_ret)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[tmp_path])},
        ):
            with patch("os.listdir", return_value=["iptables.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_iptables_runner.iptables("minion") is True
                    open_mock.assert_has_calls(expected_calls, any_order=True)


# pylint: enable=line-too-long
