# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
# pylint: disable=line-too-long
import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.runners.salt_describe_cron as salt_describe_cron_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_cron_runner: {
            "__salt__": {"salt.execute": MagicMock()},
            "__opts__": {},
        },
    }


def test_cron(tmp_path):
    cron_ret = {
        "minion": {
            "pre": [
                '10 12 * * 4 echo "hello there!"',
                '#10 12 * * 3 echo "goodbye there!"',
                '@weekly echo "special pre cron"',
                "FENDER=STRATOCASTER",
                "# THIS= BAD",
                "",
            ],
            "crons": [
                {
                    "minute": "*",
                    "hour": "*",
                    "daymonth": "*",
                    "month": "*",
                    "dayweek": "1",
                    "identifier": "SALT_CRON_JOB",
                    "cmd": "echo foobar",
                    "comment": "-- salt lol --",
                    "commented": False,
                },
                {
                    "minute": "*",
                    "hour": "*",
                    "daymonth": "*",
                    "month": "*",
                    "dayweek": "1",
                    "identifier": "commented_cron",
                    "cmd": "echo this is commented",
                    "comment": "This is a comment on a commented cron job",
                    "commented": True,
                },
            ],
            "special": [
                {
                    "spec": "@weekly",
                    "cmd": "echo silly goose",
                    "identifier": "SILLY CRON",
                    "comment": None,
                    "commented": True,
                },
            ],
            "env": [
                {
                    "name": "SALT",
                    "value": "DESCRIBE",
                },
                {
                    "name": "HELLO",
                    "value": "to the world",
                },
            ],
        },
    }

    expected_sls = {
        "FENDER": {
            "cron.env_present": [
                {"value": "STRATOCASTER"},
                {"user": "fake_user"},
            ]
        },
        "HELLO": {
            "cron.env_present": [
                {"value": "to the world"},
                {"user": "fake_user"},
            ]
        },
        "SALT": {
            "cron.env_present": [
                {"value": "DESCRIBE"},
                {"user": "fake_user"},
            ]
        },
        'echo "goodbye there!"': {
            "cron.present": [
                {"minute": "10"},
                {"hour": "12"},
                {"daymonth": "*"},
                {"month": "*"},
                {"dayweek": "3"},
                {"comment": None},
                {"identifier": False},
                {"commented": True},
                {"user": "fake_user"},
            ]
        },
        'echo "hello there!"': {
            "cron.present": [
                {"minute": "10"},
                {"hour": "12"},
                {"daymonth": "*"},
                {"month": "*"},
                {"dayweek": "4"},
                {"comment": None},
                {"identifier": False},
                {"commented": False},
                {"user": "fake_user"},
            ]
        },
        'echo "special pre cron"': {
            "cron.present": [
                {"special": "@weekly"},
                {"comment": None},
                {"commented": False},
                {"identifier": False},
                {"user": "fake_user"},
            ]
        },
        "echo foobar": {
            "cron.present": [
                {"user": "fake_user"},
                {"minute": "*"},
                {"hour": "*"},
                {"daymonth": "*"},
                {"month": "*"},
                {"dayweek": "1"},
                {"comment": "-- salt lol --"},
                {"commented": False},
                {"identifier": "SALT_CRON_JOB"},
            ]
        },
        "echo silly goose": {
            "cron.present": [
                {"user": "fake_user"},
                {"comment": None},
                {"commented": True},
                {"identifier": "SILLY CRON"},
                {"special": "@weekly"},
            ]
        },
        "echo this is commented": {
            "cron.present": [
                {"user": "fake_user"},
                {"minute": "*"},
                {"hour": "*"},
                {"daymonth": "*"},
                {"month": "*"},
                {"dayweek": "1"},
                {"comment": "This is a comment on a commented cron job"},
                {"commented": True},
                {"identifier": "commented_cron"},
            ]
        },
    }

    user = "fake_user"
    cron_sls = yaml.dump(expected_sls)

    with patch.dict(
        salt_describe_cron_runner.__salt__, {"salt.execute": MagicMock(return_value=cron_ret)}
    ):
        with patch.object(salt_describe_cron_runner, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_cron_runner.cron("minion", user)
            generate_mock.assert_called_with(
                {}, "minion", cron_sls, sls_name="cron", config_system="salt"
            )


def test_cron_crontab_unavailable(tmp_path):
    cron_ret = {
        "minion": "'cron' __virtual__ returned False: Cannot load cron module: crontab command not found"
    }

    user = "fake_user"
    with patch.dict(
        salt_describe_cron_runner.__salt__, {"salt.execute": MagicMock(return_value=cron_ret)}
    ):
        with patch.object(salt_describe_cron_runner, "generate_files") as generate_mock:
            assert not salt_describe_cron_runner.cron("minion", user)


# pylint: enable=line-too-long
