# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import json
import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.runners.salt_describe_user as salt_describe_user_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_user_runner: {
            "__salt__": {"salt.execute": MagicMock()},
            "__opts__": {},
        },
    }


def test_group():
    group_getent = {
        "minion": [
            {"gid": 4, "members": ["syslog", "whytewolf"], "name": "adm", "passwd": "x"},
            {"gid": 0, "members": [], "name": "root", "passwd": "x"},
        ]
    }

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
        salt_describe_user_runner.__salt__, {"salt.execute": MagicMock(return_value=group_getent)}
    ):
        with patch.object(salt_describe_user_runner, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_user_runner.group("minion")
            generate_mock.assert_called_with(
                {}, "minion", group_sls, sls_name="groups", config_system="salt"
            )


def test_user():
    user_getent = {
        "minion": [
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
    }

    user_shadow = {
        "minion": {
            "expire": -1,
            "inact": -1,
            "lstchg": 19103,
            "max": 99999,
            "min": 0,
            "name": "testuser",
            "passwd": "$5$k69zJBp1LxA3q8az$XKEp1knAex0j.xoi/sdU4XllHpZ0JzYYRfASKGl6qZA",
            "warn": 7,
        }
    }

    fileexists = {"minion": True}

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
        salt_describe_user_runner.__salt__,
        {"salt.execute": MagicMock(side_effect=[user_getent, user_shadow, fileexists])},
    ):
        with patch.object(salt_describe_user_runner, "generate_files") as generate_files_mock:
            with patch.object(
                salt_describe_user_runner, "generate_pillars"
            ) as generate_pillars_mock:
                assert "Generated SLS file locations" in salt_describe_user_runner.user("minion")
                generate_files_mock.assert_called_with(
                    {}, "minion", user_sls, sls_name="users", config_system="salt"
                )
                generate_pillars_mock.assert_called_with(
                    {}, "minion", user_pillar, sls_name="users"
                )
