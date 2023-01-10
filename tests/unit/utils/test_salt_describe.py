# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import MagicMock
from unittest.mock import patch

import saltext.salt_describe.utils.salt_describe as salt_describe_util
import yaml


def test_get_state_file_root(tmp_path):
    opts = {
        "file_roots": {"base": [tmp_path / "base"], "prod": [tmp_path / "prod", tmp_path / "fake"]},
    }

    assert salt_describe_util.get_state_file_root(opts, env="prod") == tmp_path / "prod"


def test_get_minion_state_file_root(tmp_path):
    with patch.object(salt_describe_util, "get_state_file_root", return_value=tmp_path / "prod"):
        assert (
            salt_describe_util.get_minion_state_file_root({}, "minion", env="prod")
            == tmp_path / "prod" / "minion"
        )


def test_get_pillar_file_root(tmp_path):
    opts = {
        "pillar_roots": {
            "base": [tmp_path / "base"],
            "prod": [tmp_path / "prod", tmp_path / "fake"],
        },
    }

    assert salt_describe_util.get_pillar_file_root(opts, env="prod") == tmp_path / "prod"


def test_get_minion_pillar_file_root(tmp_path):
    with patch.object(salt_describe_util, "get_pillar_file_root", return_value=tmp_path / "prod"):
        assert (
            salt_describe_util.get_minion_pillar_file_root({}, "minion", env="prod")
            == tmp_path / "prod" / "minion"
        )


def test_generate_files(tmp_path):
    state_contents = {
        "salt://testfile": {
            "file.managed": {
                "source": "salt://minion/files/testfile",
            },
        },
    }
    state = yaml.dump(state_contents)
    minion_state_root = tmp_path / "prod" / "minion"
    with patch.object(
        salt_describe_util, "get_minion_state_file_root", return_value=minion_state_root
    ):
        with patch.object(salt_describe_util, "generate_init", MagicMock()) as init_mock:
            sls_file = minion_state_root / "file.sls"
            assert (
                salt_describe_util.generate_files({}, "minion", state, sls_name="file", env="prod")
            ) == sls_file
            assert sls_file.exists()
            assert yaml.safe_load(sls_file.read_text()) == state_contents
            init_mock.assert_called_with({}, "minion", env="prod")


def test_generate_init(tmp_path):
    minion_state_root = tmp_path / "prod" / "minion"
    expected_init = {
        "include": ["minion.file"],
    }
    minion_state_root.mkdir(parents=True, exist_ok=True)
    (minion_state_root / "file.sls").touch()
    with patch.object(
        salt_describe_util, "get_minion_state_file_root", return_value=minion_state_root
    ):
        assert salt_describe_util.generate_init({}, "minion", env="prod") is True
        init_sls = minion_state_root / "init.sls"
        assert init_sls.exists()
        assert yaml.safe_load(init_sls.read_text()) == expected_init


def test_generate_pillars(tmp_path):
    pillar_contents = {
        "users": {"salt": "salty_passwd!"},
    }
    pillar = yaml.dump(pillar_contents)
    minion_pillar_root = tmp_path / "prod" / "minion"
    with patch.object(
        salt_describe_util, "get_minion_pillar_file_root", return_value=minion_pillar_root
    ):
        with patch.object(salt_describe_util, "generate_pillar_init", MagicMock()) as init_mock:
            assert (
                salt_describe_util.generate_pillars(
                    {}, "minion", pillar, sls_name="users", env="prod"
                )
                is True
            )
            pillar_file = minion_pillar_root / "users.sls"
            assert pillar_file.exists()
            assert yaml.safe_load(pillar_file.read_text()) == pillar_contents
            init_mock.assert_called_with({}, "minion", env="prod")


def test_generate_pillar_init(tmp_path):
    minion_pillar_root = tmp_path / "prod" / "minion"
    expected_init = {
        "include": ["minion.users"],
    }
    minion_pillar_root.mkdir(parents=True, exist_ok=True)
    (minion_pillar_root / "users.sls").touch()
    with patch.object(
        salt_describe_util, "get_minion_pillar_file_root", return_value=minion_pillar_root
    ):
        assert salt_describe_util.generate_pillar_init({}, "minion", env="prod") is True
        init_sls = minion_pillar_root / "init.sls"
        assert init_sls.exists()
        assert yaml.safe_load(init_sls.read_text()) == expected_init
