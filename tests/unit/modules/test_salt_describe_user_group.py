# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import json
import logging
from pathlib import PosixPath
from pathlib import WindowsPath
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.modules.salt_describe_user as salt_describe_user_module
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_user_module: {
            "__salt__": {"config.get": MagicMock(return_value="minion")},
            "__opts__": {},
        },
    }


def test_group():
    group_getent = [
        {"gid": 4, "members": ["syslog", "whytewolf"], "name": "adm", "passwd": "x"},
        {"gid": 0, "members": [], "name": "root", "passwd": "x"},
    ]

    group_sls_contents = {
        "group-adm": {
            "group.present": [
                {"name": "adm"},
                {"gid": 4},
            ],
        },
        "group-root": {
            "group.present": [
                {"name": "root"},
                {"gid": 0},
            ],
        },
    }

    group_sls = yaml.dump(group_sls_contents)

    with patch.dict(
        salt_describe_user_module.__salt__, {"group.getent": MagicMock(return_value=group_getent)}
    ):
        with patch.object(salt_describe_user_module, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_user_module.group()
            generate_mock.assert_called_with(
                {}, "minion", group_sls, sls_name="groups", config_system="salt"
            )


def test_user():
    user_getent = [
        {
            "name": "testuser",
            "uid": 1000,
            "gid": 1000,
            "groups": ["adm"],
            "home": "/home/testuser",
            "passwd": "x",
            "shell": "/usr/bin/zsh",
            "fullname": "",
            "homephone": "",
            "other": "",
            "roomnumber": "",
            "workphone": "",
        }
    ]

    user_shadow = {
        "expire": -1,
        "inact": -1,
        "lstchg": 19103,
        "max": 99999,
        "min": 0,
        "name": "testuser",
        "passwd": "$5$k69zJBp1LxA3q8az$XKEp1knAex0j.xoi/sdU4XllHpZ0JzYYRfASKGl6qZA",
        "warn": 7,
    }

    fileexists = True

    user_sls_contents = {
        "user-testuser": {
            "user.present": [
                {"name": "testuser"},
                {"uid": 1000},
                {"gid": 1000},
                {"allow_uid_change": True},
                {"allow_gid_change": True},
                {"home": "/home/testuser"},
                {"shell": "/usr/bin/zsh"},
                {"groups": ["adm"]},
                {"password": '{{ salt["pillar.get"]("users:testuser","*") }}'},
                {"enforce_password": True},
                {"date": 19103},
                {"mindays": 0},
                {"maxdays": 99999},
                {"inactdays": -1},
                {"expire": -1},
                {"createhome": True},
            ]
        }
    }

    user_sls = yaml.dump(user_sls_contents)

    user_pillar_contents = {
        "users": {"testuser": "$5$k69zJBp1LxA3q8az$XKEp1knAex0j.xoi/sdU4XllHpZ0JzYYRfASKGl6qZA"},
    }

    user_pillar = yaml.dump(user_pillar_contents)

    with patch.dict(
        salt_describe_user_module.__salt__,
        {"user.getent": MagicMock(return_value=user_getent)},
    ), patch.dict(
        salt_describe_user_module.__salt__,
        {"shadow.info": MagicMock(return_value=user_shadow)},
    ), patch.dict(
        salt_describe_user_module.__salt__,
        {"file.directory_exists": MagicMock(return_value=fileexists)},
    ):
        with patch.object(salt_describe_user_module, "generate_files") as generate_files_mock:
            with patch.object(
                salt_describe_user_module, "generate_pillars"
            ) as generate_pillars_mock:
                assert "Generated SLS file locations" in salt_describe_user_module.user()
                generate_files_mock.assert_called_with(
                    {}, "minion", user_sls, sls_name="users", config_system="salt"
                )
                generate_pillars_mock.assert_called_with(
                    {}, "minion", user_pillar, sls_name="users"
                )


def test_user_minimum_maximum_uid():
    user_getent = [
        {
            "name": "testuser",
            "uid": 1000,
            "gid": 1000,
            "groups": ["adm"],
            "home": "/home/testuser",
            "passwd": "x",
            "shell": "/usr/bin/zsh",
            "fullname": "",
            "homephone": "",
            "other": "",
            "roomnumber": "",
            "workphone": "",
        },
        {
            "name": "testuser2",
            "uid": 1001,
            "gid": 1001,
            "groups": ["adm"],
            "home": "/home/testuser2",
            "passwd": "x",
            "shell": "/usr/bin/zsh",
            "fullname": "",
            "homephone": "",
            "other": "",
            "roomnumber": "",
            "workphone": "",
        },
        {
            "name": "testuser3",
            "uid": 1002,
            "gid": 1002,
            "groups": ["adm"],
            "home": "/home/testuser3",
            "passwd": "x",
            "shell": "/usr/bin/zsh",
            "fullname": "",
            "homephone": "",
            "other": "",
            "roomnumber": "",
            "workphone": "",
        },
    ]

    user_shadow = {
        "expire": -1,
        "inact": -1,
        "lstchg": 19103,
        "max": 99999,
        "min": 0,
        "name": "testuser",
        "passwd": "$5$k69zJBp1LxA3q8az$XKEp1knAex0j.xoi/sdU4XllHpZ0JzYYRfASKGl6qZA",
        "warn": 7,
    }
    user_shadow2 = {
        "expire": -1,
        "inact": -1,
        "lstchg": 19103,
        "max": 99999,
        "min": 0,
        "name": "testuser",
        "passwd": "$5$k69zJBp1LxA3q8az$XKEp1knAex0j.xoi/sdU4XllHpZ0JzYYRfASKGl6qZA",
        "warn": 7,
    }
    user_shadow3 = {
        "expire": -1,
        "inact": -1,
        "lstchg": 19103,
        "max": 99999,
        "min": 0,
        "name": "testuser",
        "passwd": "$5$k69zJBp1LxA3q8az$XKEp1knAex0j.xoi/sdU4XllHpZ0JzYYRfASKGl6qZA",
        "warn": 7,
    }

    fileexists = True

    user_sls_contents = {
        "user-testuser": {
            "user.present": [
                {"name": "testuser"},
                {"uid": 1000},
                {"gid": 1000},
                {"allow_uid_change": True},
                {"allow_gid_change": True},
                {"home": "/home/testuser"},
                {"shell": "/usr/bin/zsh"},
                {"groups": ["adm"]},
                {"password": '{{ salt["pillar.get"]("users:testuser","*") }}'},
                {"enforce_password": True},
                {"date": 19103},
                {"mindays": 0},
                {"maxdays": 99999},
                {"inactdays": -1},
                {"expire": -1},
                {"createhome": True},
            ]
        }
    }

    user_sls = yaml.dump(user_sls_contents)

    user_pillar_contents = {
        "users": {"testuser": "$5$k69zJBp1LxA3q8az$XKEp1knAex0j.xoi/sdU4XllHpZ0JzYYRfASKGl6qZA"},
    }

    user_pillar = yaml.dump(user_pillar_contents)

    with patch.dict(
        salt_describe_user_module.__salt__,
        {"user.getent": MagicMock(return_value=user_getent)},
    ), patch.dict(
        salt_describe_user_module.__salt__,
        {"shadow.info": MagicMock(side_effect=[user_shadow, user_shadow2, user_shadow3])},
    ), patch.dict(
        salt_describe_user_module.__salt__,
        {"file.directory_exists": MagicMock(return_value=fileexists)},
    ):
        with patch.object(salt_describe_user_module, "generate_files") as generate_files_mock:
            with patch.object(
                salt_describe_user_module, "generate_pillars"
            ) as generate_pillars_mock:
                assert "Generated SLS file locations" in salt_describe_user_module.user(
                    minimum_uid=999, maximum_uid=1001
                )
                generate_files_mock.assert_called_with(
                    {}, "minion", user_sls, sls_name="users", config_system="salt"
                )
                generate_pillars_mock.assert_called_with(
                    {}, "minion", user_pillar, sls_name="users"
                )


def test_group_permission_denied(minion_opts, caplog, perm_denied_error_log):
    group_getent = [
        {"gid": 4, "members": ["syslog", "whytewolf"], "name": "adm", "passwd": "x"},
        {"gid": 0, "members": [], "name": "root", "passwd": "x"},
    ]

    with patch.dict(
        salt_describe_user_module.__salt__, {"group.getent": MagicMock(return_value=group_getent)}
    ):
        with patch.dict(salt_describe_user_module.__opts__, minion_opts):
            with patch.object(PosixPath, "mkdir", side_effect=PermissionError), patch.object(
                WindowsPath, "mkdir", side_effect=PermissionError
            ):
                with caplog.at_level(logging.WARNING):
                    ret = salt_describe_user_module.group()
                    assert not ret
                    assert perm_denied_error_log in caplog.text


def test_user_permission_denied(minion_opts, caplog, perm_denied_error_log):
    user_getent = [
        {
            "name": "testuser",
            "uid": 1000,
            "gid": 1000,
            "groups": ["adm"],
            "home": "/home/testuser",
            "passwd": "x",
            "shell": "/usr/bin/zsh",
            "fullname": "",
            "homephone": "",
            "other": "",
            "roomnumber": "",
            "workphone": "",
        }
    ]

    user_shadow = {
        "expire": -1,
        "inact": -1,
        "lstchg": 19103,
        "max": 99999,
        "min": 0,
        "name": "testuser",
        "passwd": "$5$k69zJBp1LxA3q8az$XKEp1knAex0j.xoi/sdU4XllHpZ0JzYYRfASKGl6qZA",
        "warn": 7,
    }

    fileexists = True

    user_pillar_contents = {
        "users": {"testuser": "$5$k69zJBp1LxA3q8az$XKEp1knAex0j.xoi/sdU4XllHpZ0JzYYRfASKGl6qZA"},
    }

    with patch.dict(
        salt_describe_user_module.__salt__,
        {"user.getent": MagicMock(return_value=user_getent)},
    ), patch.dict(
        salt_describe_user_module.__salt__,
        {"shadow.info": MagicMock(return_value=user_shadow)},
    ), patch.dict(
        salt_describe_user_module.__salt__,
        {"file.directory_exists": MagicMock(return_value=fileexists)},
    ):
        with patch.dict(salt_describe_user_module.__opts__, minion_opts):
            with patch.object(PosixPath, "mkdir", side_effect=PermissionError), patch.object(
                WindowsPath, "mkdir", side_effect=PermissionError
            ):
                with caplog.at_level(logging.WARNING):
                    ret = salt_describe_user_module.user()
                    assert not ret
                    assert perm_denied_error_log in caplog.text
