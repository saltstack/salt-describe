# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.runners.salt_describe_host as salt_describe_host_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_host_runner: {
            "__salt__": {"salt.execute": MagicMock()},
            "__opts__": {},
        },
    }


def test_host():
    """
    test describe.host
    """
    host_list = {
        "minion": {
            "comment-0": ["# Host addresses"],
            "comment-1": ["# comment"],
            "127.0.0.1": {"aliases": ["localhost"]},
            "127.0.1.1": {"aliases": ["megan-precision5550"]},
            "::1": {"aliases": ["localhost", "ip6-localhost", "ip6-loopback"]},
            "ff02::1": {"aliases": ["ip6-allnodes"]},
            "ff02::2": {"aliases": ["ip6-allrouters"]},
        }
    }

    host_sls_contents = {
        "host_file_content_0": {"host.present": [{"ip": "127.0.0.1"}, {"names": ["localhost"]}]},
        "host_file_content_1": {
            "host.present": [{"ip": "127.0.1.1"}, {"names": ["megan-precision5550"]}]
        },
        "host_file_content_2": {
            "host.present": [
                {"ip": "::1"},
                {"names": ["localhost", "ip6-localhost", "ip6-loopback"]},
            ]
        },
        "host_file_content_3": {"host.present": [{"ip": "ff02::1"}, {"names": ["ip6-allnodes"]}]},
        "host_file_content_4": {"host.present": [{"ip": "ff02::2"}, {"names": ["ip6-allrouters"]}]},
    }
    host_sls = yaml.dump(host_sls_contents)

    with patch.dict(
        salt_describe_host_runner.__salt__, {"salt.execute": MagicMock(return_value=host_list)}
    ):
        with patch.object(salt_describe_host_runner, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_host_runner.host("minion")
            generate_mock.assert_called_with(
                {}, "minion", host_sls, sls_name="host", config_system="salt"
            )
