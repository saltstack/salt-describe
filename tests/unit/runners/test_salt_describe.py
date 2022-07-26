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
import saltext.salt_describe.runners.salt_describe_cron as salt_describe_cron_runner
import saltext.salt_describe.runners.salt_describe_file as salt_describe_file_runner
import saltext.salt_describe.runners.salt_describe_firewalld as salt_describe_firewalld_runner
import saltext.salt_describe.runners.salt_describe_host as salt_describe_host_runner
import saltext.salt_describe.runners.salt_describe_iptables as salt_describe_iptables_runner
import saltext.salt_describe.runners.salt_describe_pip as salt_describe_pip_runner
import saltext.salt_describe.runners.salt_describe_pkg as salt_describe_pkg_runner
import saltext.salt_describe.runners.salt_describe_pkgrepo as salt_describe_pkgrepo_runner
import saltext.salt_describe.runners.salt_describe_service as salt_describe_service_runner
import saltext.salt_describe.runners.salt_describe_sysctl as salt_describe_sysctl_runner
import saltext.salt_describe.runners.salt_describe_timezone as salt_describe_timezone_runner
import saltext.salt_describe.runners.salt_describe_user as salt_describe_user_runner
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
        salt_describe_cron_runner: module_globals,
        salt_describe_file_runner: module_globals,
        salt_describe_firewalld_runner: module_globals,
        salt_describe_host_runner: module_globals,
        salt_describe_iptables_runner: module_globals,
        salt_describe_pip_runner: module_globals,
        salt_describe_pkg_runner: module_globals,
        salt_describe_pkgrepo_runner: module_globals,
        salt_describe_service_runner: module_globals,
        salt_describe_sysctl_runner: module_globals,
        salt_describe_timezone_runner: module_globals,
        salt_describe_user_runner: module_globals,
    }


def test_all(tmp_path):
    """
    test describe.all
    """
    group_getent = {
        "minion": [
            {"gid": 4, "members": ["syslog", "vecna"], "name": "adm", "passwd": "x"},
            {"gid": 0, "members": [], "name": "root", "passwd": "x"},
        ]
    }

    pkg_list = {
        "minion": {
            "pkg1": "0.1.2-3",
            "pkg2": "1.2rc5-3",
            "pkg3": "2.3.4-5",
        }
    }

    expected_group_sls = {
        "group-adm": {
            "group.present": [{"name": "adm"}, {"gid": 4}],
        },
        "group-root": {
            "group.present": [{"name": "root"}, {"gid": 0}],
        },
    }
    expected_group_write = yaml.dump(expected_group_sls)

    expected_pkg_sls = {
        "installed_packages": {
            "pkg.installed": [{"pkgs": [{key: value} for key, value in pkg_list["minion"].items()]}]
        }
    }
    expected_pkg_write = yaml.dump(expected_pkg_sls)

    expected_init_sls = {"include": ["minion.groups", "minion.pkg"]}
    expected_init_write = yaml.dump(expected_init_sls)

    dunder_salt_mock = {
        "salt.execute": MagicMock(side_effect=[group_getent, pkg_list]),
        "describe.cron": salt_describe_cron_runner.cron,
        "describe.file": salt_describe_file_runner.file,
        "describe.filewalld": salt_describe_firewalld_runner.firewalld,
        "describe.group": salt_describe_user_runner.group,
        "describe.host": salt_describe_host_runner.host,
        "describe.iptables": salt_describe_iptables_runner.iptables,
        "describe.pip": salt_describe_pip_runner.pip,
        "describe.pkg": salt_describe_pkg_runner.pkg,
        "describe.pkgrepo": salt_describe_pkgrepo_runner.pkgrepo,
        "describe.service": salt_describe_service_runner.service,
        "describe.sysctl": salt_describe_sysctl_runner.sysctl,
        "describe.timezone": salt_describe_timezone_runner.timezone,
        "describe.user": salt_describe_user_runner.user,
    }

    expected_calls = [
        call().write(expected_group_write),
        call().write(expected_pkg_write),
        call().write(expected_init_write),
    ]

    with patch.dict(salt_describe_runner.__salt__, dunder_salt_mock):

        exclude_list = [
            "cron",
            "file",
            "filewalld",
            "group",
            "host",
            "iptables",
            "pip",
            "pkg",
            "pkgrepo",
            "service",
            "sysctl",
            "timezone",
            "user",
        ]

        exclude_list.remove("pkg")
        exclude_list.remove("group")

        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[str(tmp_path)])},
        ):
            with patch("os.listdir", return_value=["groups.sls", "pkg.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert (
                        salt_describe_runner.all("minion", top=False, exclude=exclude_list) is True
                    )
                    open_mock.assert_has_calls(expected_calls, any_order=True)
