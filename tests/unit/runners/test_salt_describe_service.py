# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging
import sys
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.runners.salt_describe_service as salt_describe_service_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_service_runner: {
            "__salt__": {"salt.execute": MagicMock()},
            "__opts__": {},
        },
    }


def test_service():
    enabled_retval = {"minion": ["salt-master", "salt-api"]}

    if sys.platform.startswith("darwin"):
        get_all = ["salt-master", "salt-minion", "salt-api"]

        service_sls_contents = {
            "salt-master": {
                "service.running": [{"enable": True}],
            },
            "salt-minion": {
                "service.running": [{"enable": False}],
            },
            "salt-api": {
                "service.dead": [{"enable": True}],
            },
        }

        status_retval = True
        execute_retvals = [enabled_retval, get_all, status_retval]
    else:
        service_sls_contents = {
            "salt-master": {
                "service.running": [{"enable": True}],
            },
            "salt-minion": {
                "service.running": [{"enable": False}],
            },
            "salt-api": {
                "service.dead": [{"enable": True}],
            },
            "random-service": {
                "service.running": [],
            },
        }

        status_retval = {
            "minion": {
                "salt-master": True,
                "salt-minion": True,
                "salt-api": False,
                "random-service": True,
            },
        }
        disabled_retval = {"minion": ["salt-minion"]}

        execute_retvals = [enabled_retval, disabled_retval, status_retval]

    service_sls = yaml.dump(service_sls_contents)

    with patch.dict(
        salt_describe_service_runner.__salt__,
        {"salt.execute": MagicMock(side_effect=execute_retvals)},
    ):
        with patch.object(salt_describe_service_runner, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_service_runner.service("minion")
            generate_mock.assert_called_with(
                {}, "minion", service_sls, sls_name="service", config_system="salt"
            )


def test_service_ansible():

    enabled_retval = {"minion": ["salt-master", "salt-api"]}
    if sys.platform.startswith("darwin"):
        get_all = ["salt-master", "salt-minion", "salt-api"]

        service_sls_contents = {
            "salt-master": {
                "service.running": [{"enable": True}],
            },
            "salt-minion": {
                "service.running": [{"enable": False}],
            },
            "salt-api": {
                "service.dead": [{"enable": True}],
            },
        }

        status_retval = True
        execute_retvals = [enabled_retval, get_all, status_retval]
    else:
        service_sls_contents = {
            "salt-master": {
                "service.running": [{"enable": True}],
            },
            "salt-minion": {
                "service.running": [{"enable": False}],
            },
            "salt-api": {
                "service.dead": [{"enable": True}],
            },
            "random-service": {
                "service.running": [],
            },
        }

        status_retval = {
            "minion": {
                "salt-master": True,
                "salt-minion": True,
                "salt-api": False,
                "random-service": True,
            },
        }
        disabled_retval = {"minion": ["salt-minion"]}

        execute_retvals = [enabled_retval, disabled_retval, status_retval]

    service_sls = yaml.dump(service_sls_contents)

    hosts = "testgroup"
    status_retval = {
        "minion": {
            "salt-master": True,
            "salt-minion": True,
            "salt-api": False,
            "random-service": True,
        },
    }

    service_yml_contents = [
        {
            "name": "Manage Service",
            "tasks": [
                {
                    "name": "Manage service salt-master",
                    "service": {"state": "started", "name": "salt-master", "enabled": "yes"},
                },
                {
                    "name": "Manage service salt-minion",
                    "service": {"state": "started", "name": "salt-minion", "enabled": "no"},
                },
                {
                    "name": "Manage service salt-api",
                    "service": {"state": "stopped", "name": "salt-api", "enabled": "yes"},
                },
            ],
            "hosts": "testgroup",
        }
    ]
    service_yml = yaml.dump(service_yml_contents)

    execute_retvals = [enabled_retval, disabled_retval, status_retval]
    with patch.dict(
        salt_describe_service_runner.__salt__,
        {"salt.execute": MagicMock(side_effect=execute_retvals)},
    ):
        with patch.object(salt_describe_service_runner, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in (
                salt_describe_service_runner.service("minion", config_system="ansible", hosts=hosts)
            )
            generate_mock.assert_called_with(
                {}, "minion", service_yml, sls_name="service", config_system="ansible"
            )
