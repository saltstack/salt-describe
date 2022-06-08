import pytest

from unittest.mock import patch, MagicMock, mock_open, call

import saltext.salt_describe.runners.salt_describe as salt_describe_runner

import salt.config
import salt.runners.salt as salt_runner

import logging

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
        call().write(
            "adm:\n  group.present:\n  - gid: 4\nroot:\n  group.present:\n  - gid: 0\n"
        ),
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
