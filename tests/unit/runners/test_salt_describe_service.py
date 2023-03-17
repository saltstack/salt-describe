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

    if sys.platform.startswith("darwin"):
        enabled_retval = {"minion": ["com.saltstack.salt.master", "com.saltstack.salt.minion"]}

        list_retval = {
            "minion": "PID\tStatus\tLabel\n358\t0\tcom.saltstack.salt.minion\n359\t0\tcom.saltstack.salt.master\n"
        }

        service_sls_contents = {
            "com.saltstack.salt.master": {
                "service.running": [{"enable": True}],
            },
            "com.saltstack.salt.minion": {
                "service.running": [{"enable": True}],
            },
        }

        disabled_retval = {"minion": "'service.get_disabled' is not available."}

        execute_retvals = [enabled_retval, disabled_retval, list_retval]
    else:
        enabled_retval = {"minion": ["salt-master", "salt-api"]}

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

    if sys.platform.startswith("darwin"):
        enabled_retval = {"minion": ["com.saltstack.salt.master", "com.saltstack.salt.minion"]}

        list_retval = {
            "minion": "PID\tStatus\tLabel\n358\t0\tcom.saltstack.salt.minion\n359\t0\tcom.saltstack.salt.master\n"
        }

        service_yml_contents = [
            {
                "name": "Manage Service",
                "tasks": [
                    {
                        "name": "Manage service com.saltstack.salt.minion",
                        "service": {
                            "state": "started",
                            "name": "com.saltstack.salt.minion",
                            "enabled": "yes",
                        },
                    },
                    {
                        "name": "Manage service com.saltstack.salt.master",
                        "service": {
                            "state": "started",
                            "name": "com.saltstack.salt.master",
                            "enabled": "yes",
                        },
                    },
                ],
                "hosts": "testgroup",
            }
        ]

        disabled_retval = {"minion": "'service.get_disabled' is not available."}

        execute_retvals = [enabled_retval, disabled_retval, list_retval]
    else:
        enabled_retval = {"minion": ["salt-master", "salt-api"]}

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

    hosts = "testgroup"

    service_yml = yaml.dump(service_yml_contents)

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


def test_service_chef():

    if sys.platform.startswith("darwin"):
        enabled_retval = {"minion": ["com.saltstack.salt.master", "com.saltstack.salt.minion"]}

        list_retval = {
            "minion": "PID\tStatus\tLabel\n358\t0\tcom.saltstack.salt.minion\n359\t0\tcom.saltstack.salt.master\n"
        }

        service_rb_contents = """service 'com.saltstack.salt.minion' do
  action [ :enable, :start ]
end

service 'com.saltstack.salt.master' do
  action [ :enable, :start ]
end
"""

        disabled_retval = {"minion": "'service.get_disabled' is not available."}

        execute_retvals = [enabled_retval, disabled_retval, list_retval]
    else:

        enabled_retval = {"minion": ["salt-master", "salt-api"]}
        disabled_retval = {"minion": ["salt-minion"]}
        status_retval = {
            "minion": {
                "salt-master": True,
                "salt-minion": True,
                "salt-api": False,
                "random-service": True,
            },
        }

        service_rb_contents = """service 'salt-master' do
  action [ :enable, :start ]
end

service 'salt-minion' do
  action [ :disable, :start ]
end

service 'salt-api' do
  action [ :enable, :stop ]
end

service 'random-service' do
  action [ :start ]
end
"""

        execute_retvals = [enabled_retval, disabled_retval, status_retval]
    with patch.dict(
        salt_describe_service_runner.__salt__,
        {"salt.execute": MagicMock(side_effect=execute_retvals)},
    ):
        with patch.object(salt_describe_service_runner, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_service_runner.service(
                "minion", config_system="chef"
            )
            generate_mock.assert_called_with(
                {}, "minion", service_rb_contents, sls_name="service", config_system="chef"
            )
