# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest
import yaml


def test_user(salt_run_cli, minion):
    """
    Test describe.user
    """
    ret = salt_run_cli.run("describe.user", tgt=minion.id)
    if not ret.data:
        pytest.skip("Return daata is empty, skipping.")
    gen_sls = ret.data["Generated SLS file locations"][0]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert [x for x in list(data.keys()) if "user.present" in data[x]]
    assert ret.returncode == 0
