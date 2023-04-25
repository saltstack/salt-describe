# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging
from pathlib import PosixPath
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.runners.salt_describe_pip as salt_describe_pip_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_pip_runner: {
            "__salt__": {"salt.execute": MagicMock()},
            "__opts__": {},
        },
    }


def test_pip():
    pip_list = {
        "minion": [
            "requests==0.1.2",
            "salt==3004.1",
            "argcomplete==2.3.4-5",
        ],
    }

    expected_sls_write = yaml.dump(
        {
            "installed_pip_libraries": {"pip.installed": [{"pkgs": pip_list["minion"]}]},
        }
    )
    with patch.dict(
        salt_describe_pip_runner.__salt__, {"salt.execute": MagicMock(return_value=pip_list)}
    ):
        with patch.object(salt_describe_pip_runner, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in salt_describe_pip_runner.pip("minion")
            generate_mock.assert_called_with(
                {}, "minion", expected_sls_write, sls_name="pip", config_system="salt"
            )


def test_pip_ansible():
    hosts = "testgroup"
    pip_list = {
        "minion": [
            "requests==0.1.2",
            "salt==3004.1",
            "argcomplete==2.3.4-5",
        ],
    }

    expected_yml_write = yaml.dump(
        [
            {
                "tasks": [
                    {
                        "name": "installed_pip_libraries",
                        "ansible.builtin.pip": {
                            "name": ["requests==0.1.2", "salt==3004.1", "argcomplete==2.3.4-5"]
                        },
                    }
                ],
                "hosts": "testgroup",
            }
        ]
    )
    with patch.dict(
        salt_describe_pip_runner.__salt__, {"salt.execute": MagicMock(return_value=pip_list)}
    ):
        with patch.object(salt_describe_pip_runner, "generate_files") as generate_mock:
            assert "Generated SLS file locations" in (
                salt_describe_pip_runner.pip("minion", config_system="ansible", hosts=hosts)
            )
            generate_mock.assert_called_with(
                {},
                "minion",
                expected_yml_write,
                sls_name="pip",
                config_system="ansible",
            )


def test_pip_permission_denied(minion_opts, caplog):
    pip_list = {
        "minion": [
            "requests==0.1.2",
            "salt==3004.1",
            "argcomplete==2.3.4-5",
        ],
    }

    with patch.dict(
        salt_describe_pip_runner.__salt__, {"salt.execute": MagicMock(return_value=pip_list)}
    ):
        with patch.dict(salt_describe_pip_runner.__opts__, minion_opts):
            with patch.object(PosixPath, "mkdir", side_effect=PermissionError) as mock_mkdir:
                with caplog.at_level(logging.WARNING):
                    ret = salt_describe_pip_runner.pip("minion")
                    assert not ret
                    assert (
                        "Unable to create directory /srv/salt/minion.  "
                        "Check that the salt user has the correct permissions."
                    ) in caplog.text
