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
import saltext.salt_describe.runners.salt_describe_firewalld as salt_describe_firewalld_runner
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
        salt_describe_firewalld_runner: module_globals,
    }


def test_firewalld(tmp_path):
    """
    test describe.firewalld
    """
    firewalld_ret = {
        "poc-minion": {
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
    }

    expected_content = {
        "add_firewalld_rule_0": {
            "firewalld.present": [{"name": "public"}, {"services": ["dhcpv6-client", "ssh"]}]
        }
    }

    expected_sls_write = yaml.dump(expected_content)
    expected_include_write = yaml.dump({"include": ["poc-minion.firewalld"]})
    expected_calls = [
        call().write(expected_sls_write),
        call().write(expected_include_write),
    ]

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=firewalld_ret)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[tmp_path])},
        ):
            with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                with patch("os.listdir", return_value=["firewalld.sls"]):
                    assert salt_describe_firewalld_runner.firewalld("minion") is True
                    open_mock.assert_has_calls(expected_calls, any_order=True)


# pylint: enable=line-too-long
