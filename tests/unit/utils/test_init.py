# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.utils.init as describe_util
import yaml


@pytest.mark.parametrize(
    "config_system",
    [
        "salt",
    ],
)
def test_generate_files(tmp_path, config_system):
    state_contents = {
        "salt://testfile": {
            "file.managed": {
                "source": "salt://minion/files/testfile",
            },
        },
    }
    state = yaml.dump(state_contents)
    assert describe_util.generate_files(
        {"file_roots": {"base": [tmp_path / "file_root"]}},
        "minion",
        state,
        sls_name="file",
        config_system=config_system,
    )


@pytest.mark.parametrize(
    "config_system",
    [
        "salt",
    ],
)
def test_get_minion_state_file_root(tmp_path, config_system):
    assert describe_util.get_minion_state_file_root(
        {"file_roots": {"base": [tmp_path / "file_root"]}}, "minion", config_system=config_system
    )


def test_ret_info_sls_files(tmp_path):
    """
    Test when ret_info when sls_files exist
    """
    sls_files = [tmp_path / "one.sls", tmp_path / "two.sls"]
    ret = describe_util.ret_info(sls_files)
    assert ret == {"Generated SLS file locations": sls_files}


def test_ret_info_no_sls_files(caplog):
    """
    Test when ret_info when sls_files exist
    """
    sls_files = []
    ret = describe_util.ret_info(sls_files)
    "SLS file not generated" in caplog.text
    assert ret is False


@pytest.mark.parametrize(
    "ret,exp_ret",
    [
        ("ERROR: firwalld is not running", False),
        ("Firewalld is not available", False),
        ("Ran cmd successfully", True),
    ],
)
def test_parse_salt_ret(caplog, ret, exp_ret):
    tgt = "test_minion"
    ret = {tgt: ret}
    assert describe_util.parse_salt_ret(ret=ret, tgt=tgt) is exp_ret
    if not exp_ret:
        assert ret[tgt] in caplog.text


@pytest.mark.parametrize(
    "ret,exp_ret",
    [
        ("ERROR: firwalld is not running", False),
        ("Firewalld is not available", False),
        ("Ran cmd successfully", True),
    ],
)
def test_parse_salt_multiple_ret(caplog, ret, exp_ret):
    tgt = "*"
    _ret = {
        "test_minion1": ("Ran cmd successfully", True),
        "test_minion2": ("Ran cmd successfully", True),
        "test_minion3": ret,
    }
    tgts = ["test_minion1", "test_minion2", "test_minion3"]
    assert describe_util.parse_salt_ret(ret=_ret, tgt=tgt) is exp_ret
    if not exp_ret:
        for _tgt in tgts:
            if _ret[_tgt] == ret:
                assert _ret[_tgt] in caplog.text

    tgt = "*"
    _ret = {
        "test_minion1": ("Ran cmd successfully", True),
        "test_minion2": ret,
        "test_minion3": ret,
    }
    tgts = ["test_minion1", "test_minion2", "test_minion3"]
    assert describe_util.parse_salt_ret(ret=_ret, tgt=tgt) is exp_ret
    if not exp_ret:
        for _tgt in tgts:
            if _ret[_tgt] == ret:
                assert _ret[_tgt] in caplog.text

    tgt = "*"
    _ret = {"test_minion1": ret, "test_minion2": ret, "test_minion3": ret}
    tgts = ["test_minion1", "test_minion2", "test_minion3"]
    assert describe_util.parse_salt_ret(ret=_ret, tgt=tgt) is exp_ret
    if not exp_ret:
        for _tgt in tgts:
            if _ret[_tgt] == ret:
                assert _ret[_tgt] in caplog.text
