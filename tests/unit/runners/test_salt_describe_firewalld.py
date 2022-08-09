import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.runners.salt_describe_firewalld as salt_describe_firewalld_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_firewalld_runner: {
            "__salt__": {"salt.execute": MagicMock()},
            "__opts__": {},
        },
    }


def test_firewalld():
    """
    test describe.firewalld
    """
    firewalld_ret = {
        "minion": {
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

    firewalld_sls_contents = {
        "add_firewalld_rule_0": {
            "firewalld.present": [{"name": "public"}, {"services": ["dhcpv6-client", "ssh"]}]
        }
    }
    firewalld_sls = yaml.dump(firewalld_sls_contents)

    with patch.dict(salt_describe_firewalld_runner.__salt__, {"salt.execute": MagicMock(return_value=firewalld_ret)}):
        with patch.object(salt_describe_firewalld_runner, "generate_sls") as generate_mock:
            assert salt_describe_firewalld_runner.firewalld("minion") is True
            generate_mock.assert_called_with({}, "minion", firewalld_sls, sls_name="firewalld")
