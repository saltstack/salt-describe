# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging
import sys
from pathlib import PosixPath
from pathlib import WindowsPath
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.modules.salt_describe_service as salt_describe_service_module
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_service_module: {
            "__salt__": {"config.get": MagicMock(return_value="minion")},
            "__opts__": {},
        },
    }


def test_service():

    if sys.platform.startswith("darwin"):
        enabled_retval = ["com.saltstack.salt.master", "com.saltstack.salt.minion"]

        service_status_list_func = "service.list"
        service_status_list_retval = "PID\tStatus\tLabel\n358\t0\tcom.saltstack.salt.minion\n359\t0\tcom.saltstack.salt.master\n"

        service_sls_contents = {
            "com.saltstack.salt.master": {
                "service.running": [{"enable": True}],
            },
            "com.saltstack.salt.minion": {
                "service.running": [{"enable": True}],
            },
        }

        disabled_retval = "'service.get_disabled' is not available."
    else:
        enabled_retval = ["salt-master", "salt-api"]

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

        service_status_list_func = "service.status"
        service_status_list_retval = {
            "salt-master": True,
            "salt-minion": True,
            "salt-api": False,
            "random-service": True,
        }
        disabled_retval = ["salt-minion"]

    service_sls = yaml.dump(service_sls_contents)

    with patch.dict(
        salt_describe_service_module.__salt__,
        {"service.get_enabled": MagicMock(return_value=enabled_retval)},
    ), patch.dict(
        salt_describe_service_module.__salt__,
        {"service.get_disabled": MagicMock(return_value=disabled_retval)},
    ), patch.dict(
        salt_describe_service_module.__salt__,
        {service_status_list_func: MagicMock(return_value=service_status_list_retval)},
    ):
        with patch.object(salt_describe_service_module, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_service_module.service()
            generate_mock.assert_called_with(
                {}, "minion", service_sls, sls_name="service", config_system="salt"
            )


def test_service_ansible():

    if sys.platform.startswith("darwin"):
        enabled_retval = ["com.saltstack.salt.master", "com.saltstack.salt.minion"]

        list_retval = "PID\tStatus\tLabel\n358\t0\tcom.saltstack.salt.minion\n359\t0\tcom.saltstack.salt.master\n"

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

        status_retval = {}
        disabled_retval = "'service.get_disabled' is not available."
    else:
        enabled_retval = ["salt-master", "salt-api"]

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
            "salt-master": True,
            "salt-minion": True,
            "salt-api": False,
            "random-service": True,
        }
        disabled_retval = ["salt-minion"]

    hosts = "testgroup"

    service_yml = yaml.dump(service_yml_contents)

    with patch.dict(
        salt_describe_service_module.__salt__,
        {"service.get_enabled": MagicMock(return_value=enabled_retval)},
    ), patch.dict(
        salt_describe_service_module.__salt__,
        {"service.get_disabled": MagicMock(return_value=disabled_retval)},
    ), patch.dict(
        salt_describe_service_module.__salt__,
        {"service.status": MagicMock(return_value=status_retval)},
    ):
        with patch.object(salt_describe_service_module, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in (
                salt_describe_service_module.service(config_system="ansible", hosts=hosts)
            )
            generate_mock.assert_called_with(
                {}, "minion", service_yml, sls_name="service", config_system="ansible"
            )


def test_service_chef():

    if sys.platform.startswith("darwin"):
        enabled_retval = ["com.saltstack.salt.master", "com.saltstack.salt.minion"]

        list_retval = "PID\tStatus\tLabel\n358\t0\tcom.saltstack.salt.minion\n359\t0\tcom.saltstack.salt.master\n"

        service_rb_contents = """service 'com.saltstack.salt.minion' do
  action [ :enable, :start ]
end

service 'com.saltstack.salt.master' do
  action [ :enable, :start ]
end
"""

        status_retval = {}
        disabled_retval = "'service.get_disabled' is not available."

    else:

        enabled_retval = ["salt-master", "salt-api"]
        disabled_retval = ["salt-minion"]
        status_retval = {
            "salt-master": True,
            "salt-minion": True,
            "salt-api": False,
            "random-service": True,
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

    with patch.dict(
        salt_describe_service_module.__salt__,
        {"service.get_enabled": MagicMock(return_value=enabled_retval)},
    ), patch.dict(
        salt_describe_service_module.__salt__,
        {"service.get_disabled": MagicMock(return_value=disabled_retval)},
    ), patch.dict(
        salt_describe_service_module.__salt__,
        {"service.status": MagicMock(return_value=status_retval)},
    ):
        with patch.object(salt_describe_service_module, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_service_module.service(
                config_system="chef"
            )
            generate_mock.assert_called_with(
                {}, "minion", service_rb_contents, sls_name="service", config_system="chef"
            )


def test_service_permission_denied(minion_opts, caplog, perm_denied_error_log):

    if sys.platform.startswith("darwin"):
        enabled_retval = ["com.saltstack.salt.master", "com.saltstack.salt.minion"]

        list_retval = "PID\tStatus\tLabel\n358\t0\tcom.saltstack.salt.minion\n359\t0\tcom.saltstack.salt.master\n"

        status_retval = {}
        disabled_retval = "'service.get_disabled' is not available."

    else:
        enabled_retval = ["salt-master", "salt-api"]

        status_retval = {
            "salt-master": True,
            "salt-minion": True,
            "salt-api": False,
            "random-service": True,
        }
        disabled_retval = ["salt-minion"]

    with patch.dict(
        salt_describe_service_module.__salt__,
        {"service.get_enabled": MagicMock(return_value=enabled_retval)},
    ), patch.dict(
        salt_describe_service_module.__salt__,
        {"service.get_disabled": MagicMock(return_value=disabled_retval)},
    ), patch.dict(
        salt_describe_service_module.__salt__,
        {"service.status": MagicMock(return_value=status_retval)},
    ):
        with patch.dict(salt_describe_service_module.__opts__, minion_opts):
            with patch.object(PosixPath, "mkdir", side_effect=PermissionError), patch.object(
                WindowsPath, "mkdir", side_effect=PermissionError
            ):
                with caplog.at_level(logging.WARNING):
                    ret = salt_describe_service_module.service()
                    assert not ret
                    assert perm_denied_error_log in caplog.text
