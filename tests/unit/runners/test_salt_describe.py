import logging
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
import salt.config
import salt.runners.salt as salt_runner
import saltext.salt_describe.runners.salt_describe as salt_describe_runner
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
    }


def test_pkg():
    pkg_list = {
        "minion": {
            "pkg1": "0.1.2-3",
            "pkg2": "1.2rc5-3",
            "pkg3": "2.3.4-5",
            "pk4": "3.4-5",
            "pkg5": "4.5.6-7",
        }
    }

    expected_calls = [
        call().write(
            "installed_packages:\n  pkg.installed:\n  - pkgs:\n    - pkg1: 0.1.2-3\n    - pkg2: 1.2rc5-3\n    - pkg3: 2.3.4-5\n    - pk4: 3.4-5\n    - pkg5: 4.5.6-7\n"
        ),
        call().write("include:\n- minion.pkgs\n"),
    ]
    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=pkg_list)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=["/srv/salt", "/srv/spm/salt"])},
        ):
            with patch("os.listdir", return_value=["pkgs.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_runner.pkg("minion") == True
                    open_mock.assert_has_calls(expected_calls, any_order=True)


def test_group():
    group_getent = {
        "minion": [
            {"gid": 4, "members": ["syslog", "whytewolf"], "name": "adm", "passwd": "x"},
            {"gid": 0, "members": [], "name": "root", "passwd": "x"},
        ]
    }

    expected_calls = [
        call().write("adm:\n  group.present:\n  - gid: 4\nroot:\n  group.present:\n  - gid: 0\n"),
        call().write("include:\n- minion.groups"),
    ]

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=group_getent)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=["/srv/salt", "/srv/spm/salt"])},
        ):
            with patch("os.listdir", return_value=["groups.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_runner.group("minion") == True
                    open_mock.assert_has_calls(expected_calls, any_order=True)


def test_host(tmp_path):
    """
    test describe.host
    """
    host_list = {
        "poc-minion": {
            "comment-0": ["# Host addresses"],
            "comment-1": ["# comment"],
            "127.0.0.1": {"aliases": ["localhost"]},
            "127.0.1.1": {"aliases": ["megan-precision5550"]},
            "::1": {"aliases": ["localhost", "ip6-localhost", "ip6-loopback"]},
            "ff02::1": {"aliases": ["ip6-allnodes"]},
            "ff02::2": {"aliases": ["ip6-allrouters"]},
        }
    }

    expected_content = {
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

    host_file = tmp_path / "poc-minion" / "host.sls"
    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=host_list)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[tmp_path])},
        ):
            assert salt_describe_runner.host("minion") == True
            with open(host_file) as fp:
                content = yaml.safe_load(fp.read())
                assert content == expected_content


def test_timezone(tmp_path):
    """
    test describe.host
    """
    timezone_list = {"poc-minion": "America/Los_Angeles"}

    expected_content = {"America/Los_Angeles": {"timezone.system": []}}

    host_file = tmp_path / "poc-minion" / "timezone.sls"
    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=timezone_list)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[tmp_path])},
        ):
            assert salt_describe_runner.host("minion") == True
            with open(host_file) as fp:
                content = yaml.safe_load(fp.read())
                assert content == expected_content


def test_sysctl():
    sysctl_show = {"minion": {"vm.swappiness": 60, "vm.vfs_cache_pressure": 100}}

    expected_calls = [
        call().write(
            "sysctl-vm.swappiness:\n  sysctl.present:\n  - name: vm.swappiness\n  - value: 60\n"
        ),
        call().write("include:\n- minion.sysctl\n"),
    ]

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=sysctl_show)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=["/srv/salt", "/srv/spm/salt"])},
        ):
            with patch("os.listdir", return_value=["sysctl.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_runner.sysctl("minion", ["vm.swappiness"]) == True
                    open_mock.return_value.write.assert_has_calls(expected_calls, any_order=True)


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
        "adm": {
            "group.present": [{"gid": 4}],
        },
        "root": {
            "group.present": [{"gid": 0}],
        },
    }

    expected_pkg_sls = {
        "installed_packages": {
            "pkg.installed": [{"pkgs": [{key: value} for key, value in pkg_list["minion"].items()]}]
        }
    }

    expected_init_sls = {"include": ["minion.groups", "minion.pkg"]}

    exclude_list = list(salt_describe_runner._get_all_single_describe_methods().keys())
    exclude_list.remove("pkg")
    exclude_list.remove("group")

    dunder_salt_mock = {
        "salt.execute": MagicMock(side_effect=[group_getent, pkg_list]),
        "describe.group": salt_describe_runner.group,
        "describe.pkg": salt_describe_runner.pkg,
    }

    with patch.dict(salt_describe_runner.__salt__, dunder_salt_mock):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[str(tmp_path)])},
        ):
            with patch("os.listdir", return_value=["groups.sls", "pkg.sls"]):
                assert salt_describe_runner.all("minion", top=False, exclude=exclude_list) == True
                sls_files = list(tmp_path.glob("**/*.sls"))
                expected_files = ["init", "pkg", "groups"]
                expected_sls = [expected_init_sls, expected_pkg_sls, expected_group_sls]
                for filename, sls in zip(expected_files, expected_sls):
                    sls_path = tmp_path / "minion" / f"{filename}.sls"
                    assert sls_path in sls_files
                    assert yaml.safe_load(sls_path.read_text()) == sls
