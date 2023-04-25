# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging
from pathlib import PosixPath
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.runners.salt_describe_pkg as salt_describe_pkg_runner
import saltext.salt_describe.utils.salt_describe as salt_describe_util
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_pkg_runner: {
            "__salt__": {"salt.execute": MagicMock()},
            "__opts__": {},
        },
    }


def test_pkg(minion_opts):
    pkg_list = {
        "minion": {
            "pkg1": "0.1.2-3",
            "pkg2": "1.2rc5-3",
            "pkg3": "2.3.4-5",
            "pk4": "3.4-5",
            "pkg5": "4.5.6-7",
        }
    }
    pkg_sls_contents = {
        "installed_packages": {
            "pkg.installed": [
                {"pkgs": [{name: version} for name, version in pkg_list["minion"].items()]}
            ],
        },
    }
    pkg_sls = yaml.dump(pkg_sls_contents)
    with patch.dict(
        salt_describe_pkg_runner.__salt__, {"salt.execute": MagicMock(return_value=pkg_list)}
    ):
        with patch.object(salt_describe_pkg_runner, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_pkg_runner.pkg("minion")
            generate_mock.assert_called_with(
                {}, "minion", pkg_sls, sls_name="pkg", config_system="salt"
            )


def test_pkg_permission_denied(minion_opts, caplog):
    pkg_list = {
        "minion": {
            "pkg1": "0.1.2-3",
            "pkg2": "1.2rc5-3",
            "pkg3": "2.3.4-5",
            "pk4": "3.4-5",
            "pkg5": "4.5.6-7",
        }
    }
    with patch.dict(
        salt_describe_pkg_runner.__salt__, {"salt.execute": MagicMock(return_value=pkg_list)}
    ):
        with patch.dict(salt_describe_pkg_runner.__opts__, minion_opts):
            with patch.object(PosixPath, "mkdir", side_effect=PermissionError) as mock_mkdir:
                with caplog.at_level(logging.WARNING):
                    ret = salt_describe_pkg_runner.pkg("minion")
                    assert not ret
                    assert (
                        "Unable to create directory /srv/salt/minion.  "
                        "Check that the salt user has the correct permissions."
                    ) in caplog.text


def test_pkg_ansible():
    hosts = "testgroup"
    pkg_list = {
        "minion": {
            "pkg1": "0.1.2-3",
            "pkg2": "1.2rc5-3",
            "pkg3": "2.3.4-5",
            "pk4": "3.4-5",
            "pkg5": "4.5.6-7",
        }
    }
    pkg_yml_contents = [
        {
            "tasks": [
                {
                    "name": "Package Installaion",
                    "dnf": {"name": ["pkg1", "pkg2", "pkg3", "pk4", "pkg5"]},
                }
            ],
            "hosts": "testgroup",
        }
    ]
    pkg_yml = yaml.dump(pkg_yml_contents)

    mock_minion_data = ({}, {"os_family": "RedHat"}, {})

    with patch.dict(
        salt_describe_pkg_runner.__salt__, {"salt.execute": MagicMock(return_value=pkg_list)}
    ):
        with patch(
            "salt.utils.minions.get_minion_data", MagicMock(return_value=mock_minion_data)
        ) as minion_data_mock:
            with patch.object(salt_describe_pkg_runner, "generate_files") as generate_mock:
                assert "Generated SLS file locations" in (
                    salt_describe_pkg_runner.pkg("minion", config_system="ansible", hosts=hosts)
                )
                generate_mock.assert_called_with(
                    {}, "minion", pkg_yml, sls_name="pkg", config_system="ansible"
                )

    hosts = "testgroup"
    pkg_list = {
        "minion": {
            "pkg1": "0.1.2-3",
            "pkg2": "1.2rc5-3",
            "pkg3": "2.3.4-5",
            "pk4": "3.4-5",
            "pkg5": "4.5.6-7",
        }
    }
    pkg_yml_contents = [
        {
            "tasks": [
                {
                    "name": "Package Installaion",
                    "apt": {"name": ["pkg1", "pkg2", "pkg3", "pk4", "pkg5"]},
                }
            ],
            "hosts": "testgroup",
        }
    ]
    pkg_yml = yaml.dump(pkg_yml_contents)

    mock_minion_data = ({}, {"os_family": "Debian"}, {})

    with patch.dict(
        salt_describe_pkg_runner.__salt__, {"salt.execute": MagicMock(return_value=pkg_list)}
    ):
        with patch(
            "salt.utils.minions.get_minion_data", MagicMock(return_value=mock_minion_data)
        ) as minion_data_mock:
            with patch.object(salt_describe_pkg_runner, "generate_files") as generate_mock:
                assert "Generated SLS file locations" in (
                    salt_describe_pkg_runner.pkg("minion", config_system="ansible", hosts=hosts)
                )
                generate_mock.assert_called_with(
                    {}, "minion", pkg_yml, sls_name="pkg", config_system="ansible"
                )


def test_pkg_chef():
    pkg_list = {
        "minion": {
            "pkg1": "0.1.2-3",
            "pkg2": "1.2rc5-3",
            "pkg3": "2.3.4-5",
            "pk4": "3.4-5",
            "pkg5": "4.5.6-7",
        }
    }
    pkg_rb_contents = """package 'pkg1' do
  action :install
end

package 'pkg2' do
  action :install
end

package 'pkg3' do
  action :install
end

package 'pk4' do
  action :install
end

package 'pkg5' do
  action :install
end
"""

    with patch.dict(
        salt_describe_pkg_runner.__salt__, {"salt.execute": MagicMock(return_value=pkg_list)}
    ):
        with patch.object(salt_describe_pkg_runner, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_pkg_runner.pkg(
                "minion", config_system="chef"
            )
            generate_mock.assert_called_with(
                {}, "minion", pkg_rb_contents, sls_name="pkg", config_system="chef"
            )


def test_pkg_ansible_permission_denied(minion_opts, caplog):
    pkg_list = {
        "minion": {
            "pkg1": "0.1.2-3",
            "pkg2": "1.2rc5-3",
            "pkg3": "2.3.4-5",
            "pk4": "3.4-5",
            "pkg5": "4.5.6-7",
        }
    }
    grains = {"os_family": "Debian"}
    with patch.dict(
        salt_describe_pkg_runner.__salt__, {"salt.execute": MagicMock(return_value=pkg_list)}
    ):
        with patch.dict(salt_describe_pkg_runner.__opts__, minion_opts), patch(
            "salt.utils.minions.get_minion_data",
            MagicMock(return_value=(None, grains, None)),
        ):
            with patch.object(PosixPath, "mkdir", side_effect=PermissionError) as mock_mkdir:
                with caplog.at_level(logging.WARNING):
                    ret = salt_describe_pkg_runner.pkg("minion", config_system="ansible")
                    assert not ret
                    assert (
                        "Unable to create directory /srv/ansible/minion.  "
                        "Check that the salt user has the correct permissions."
                    ) in caplog.text


def test_pkg_chef_permission_denied(minion_opts, caplog):
    pkg_list = {
        "minion": {
            "pkg1": "0.1.2-3",
            "pkg2": "1.2rc5-3",
            "pkg3": "2.3.4-5",
            "pk4": "3.4-5",
            "pkg5": "4.5.6-7",
        }
    }
    grains = {"os_family": "Debian"}
    with patch.dict(
        salt_describe_pkg_runner.__salt__, {"salt.execute": MagicMock(return_value=pkg_list)}
    ):
        with patch.dict(salt_describe_pkg_runner.__opts__, minion_opts), patch(
            "salt.utils.minions.get_minion_data",
            MagicMock(return_value=(None, grains, None)),
        ):
            with patch.object(PosixPath, "mkdir", side_effect=PermissionError) as mock_mkdir:
                with caplog.at_level(logging.WARNING):
                    ret = salt_describe_pkg_runner.pkg("minion", config_system="chef")
                    assert not ret
                    assert (
                        "Unable to create directory /srv/chef/minion.  "
                        "Check that the salt user has the correct permissions."
                    ) in caplog.text
