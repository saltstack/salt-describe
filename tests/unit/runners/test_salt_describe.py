# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
# pylint: disable=line-too-long
import inspect
import logging
from unittest.mock import create_autospec
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import salt.config  # pylint: disable=import-error
import saltext.salt_describe.runners.salt_describe as salt_describe_runner
import saltext.salt_describe.runners.salt_describe_cron as salt_describe_cron_runner
import saltext.salt_describe.runners.salt_describe_file as salt_describe_file_runner
import saltext.salt_describe.runners.salt_describe_pip as salt_describe_pip_runner
import saltext.salt_describe.runners.salt_describe_pkg as salt_describe_pkg_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_runner: {},
    }


def test_all(tmp_path):
    """
    test describe.all
    """
    cron_mock = create_autospec(salt_describe_cron_runner.cron)
    file_mock = create_autospec(salt_describe_file_runner.file)
    pip_mock = create_autospec(salt_describe_pip_runner.pip)
    pkg_mock = create_autospec(salt_describe_pkg_runner.pkg)

    cron_mock.return_value = {"generate": [str(tmp_path / "cron.sls")]}
    file_mock.return_value = {"generate": [str(tmp_path / "file.sls")]}
    pip_mock.return_value = {"generate": [str(tmp_path / "pip.sls")]}
    pkg_mock.return_value = {"generate": [str(tmp_path / "pkg.sls")]}

    all_methods = {
        "cron": cron_mock,
        "file": file_mock,
        "pip": pip_mock,
        "pkg": pkg_mock,
    }

    # Workaround for a bug in python 3.6: https://bugs.python.org/issue17185
    inspect_retvals = [
        inspect.signature(salt_describe_file_runner.file),
        inspect.signature(salt_describe_pip_runner.pip),
    ]

    with patch.object(
        salt_describe_runner, "_get_all_single_describe_methods", return_value=all_methods
    ):
        dunder_salt_mock = {
            "describe.cron": cron_mock,
            "describe.file": file_mock,
            "describe.pip": pip_mock,
            "describe.pkg": pkg_mock,
        }

        # This should only run file and pip
        with patch.dict(salt_describe_runner.__salt__, dunder_salt_mock):
            with patch.object(salt_describe_runner, "signature", side_effect=inspect_retvals):
                exclude = ["cron", "pkg"]
                assert "Generated SLS file locations" in (
                    salt_describe_runner.all_(
                        "minion",
                        top=False,
                        exclude=exclude,
                        file_paths="/fake/path",
                        bin_env="fake-env",
                    )
                )
                cron_mock.assert_not_called()
                file_mock.assert_called_with("minion", "/fake/path", config_system="salt")
                pip_mock.assert_called_with("minion", bin_env="fake-env", config_system="salt")
                pkg_mock.assert_not_called()

            with patch.object(salt_describe_runner, "signature", side_effect=inspect_retvals):
                include = ["pip", "file"]
                assert "Generated SLS file locations" in (
                    salt_describe_runner.all_(
                        "minion",
                        top=False,
                        include=include,
                        paths="/fake/path",
                        pip_bin_env="fake-env",
                    )
                )
                cron_mock.assert_not_called()
                file_mock.assert_called_with("minion", "/fake/path", config_system="salt")
                pip_mock.assert_called_with("minion", bin_env="fake-env", config_system="salt")
                pkg_mock.assert_not_called()


def test__get_all_single_describe_methods():
    dunder_salt_mock = {
        "describe.fake": MagicMock(__all_excluded__=True),
        "describe.file": MagicMock(),
        "describe.pip": MagicMock(),
    }

    # We should only get back file and pip
    with patch.dict(salt_describe_runner.__salt__, dunder_salt_mock):
        valid_funcs = salt_describe_runner._get_all_single_describe_methods()
        assert "fake" not in valid_funcs
        assert "file" in valid_funcs
        assert "pip" in valid_funcs


def test_top(tmp_path):
    gather_minions_mock = MagicMock(return_value=["minion-1", "minion-2"])
    local_mock = MagicMock(local=MagicMock(gather_minions=gather_minions_mock))
    remote_funcs_mock = MagicMock(return_value=local_mock)

    expected_contents = {
        "base": {
            "minion-0": ["minion-0.fake-sls"],
            "minion-1": ["minion-1.pip", "minion-1.cron"],
            "minion-2": ["minion-2.file", "minion-2.pkg"],
        },
    }

    with patch("salt.daemons.masterapi.RemoteFuncs", remote_funcs_mock):
        with patch.dict(
            salt_describe_runner.__salt__, {"config.get": MagicMock(return_value=[tmp_path])}
        ):
            # Put some info in the top file beforehand
            top_file = tmp_path / "top.sls"
            with salt.utils.files.fopen(top_file, "w") as fp_:
                fp_.write(yaml.dump({"base": {"minion-0": ["minion-0.fake-sls"]}}))

            # Put in some empty sls files for now
            minion_1_dir = tmp_path / "minion-1"
            minion_1_dir.mkdir()
            (minion_1_dir / "init.sls").touch()
            (minion_1_dir / "pip.sls").touch()
            (minion_1_dir / "cron.sls").touch()

            minion_2_dir = tmp_path / "minion-2"
            minion_2_dir.mkdir()
            (minion_2_dir / "file.sls").touch()
            (minion_2_dir / "pkg.sls").touch()

            salt_describe_runner.top_("minion")
            top_contents = yaml.safe_load(top_file.read_text())

            # Can't compare directly here because order of lists is inconsistent from yaml.safe_load
            for env in expected_contents:
                assert env in top_contents
                for minion in expected_contents[env]:
                    assert len(expected_contents[env][minion]) == len(top_contents[env][minion])
                    for sls in expected_contents[env][minion]:
                        assert sls in top_contents[env][minion]


def test_pillar_top(tmp_path):
    gather_minions_mock = MagicMock(return_value=["minion-1", "minion-2"])
    local_mock = MagicMock(local=MagicMock(gather_minions=gather_minions_mock))
    remote_funcs_mock = MagicMock(return_value=local_mock)

    expected_contents = {
        "base": {
            "minion-0": ["minion-0.fake-sls"],
            "minion-1": ["minion-1.pip", "minion-1.cron"],
            "minion-2": ["minion-2.file", "minion-2.pkg"],
        },
    }

    with patch("salt.daemons.masterapi.RemoteFuncs", remote_funcs_mock):
        with patch.dict(
            salt_describe_runner.__salt__, {"config.get": MagicMock(return_value=[tmp_path])}
        ):
            # Put some info in the top file beforehand
            top_file = tmp_path / "top.sls"
            with salt.utils.files.fopen(top_file, "w") as fp_:
                fp_.write(yaml.dump({"base": {"minion-0": ["minion-0.fake-sls"]}}))

            # Put in some empty sls files for now
            minion_1_dir = tmp_path / "minion-1"
            minion_1_dir.mkdir()
            (minion_1_dir / "init.sls").touch()
            (minion_1_dir / "pip.sls").touch()
            (minion_1_dir / "cron.sls").touch()

            minion_2_dir = tmp_path / "minion-2"
            minion_2_dir.mkdir()
            (minion_2_dir / "file.sls").touch()
            (minion_2_dir / "pkg.sls").touch()

            salt_describe_runner.pillar_top("minion")
            top_contents = yaml.safe_load(top_file.read_text())

            # Can't compare directly here because order of lists is inconsistent from yaml.safe_load
            for env in expected_contents:
                assert env in top_contents
                for minion in expected_contents[env]:
                    assert len(expected_contents[env][minion]) == len(top_contents[env][minion])
                    for sls in expected_contents[env][minion]:
                        assert sls in top_contents[env][minion]
