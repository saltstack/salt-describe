# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest
import yaml


def test_service(salt_run_cli, minion):
    """
    Test describe.service
    """
    ret = salt_run_cli.run("describe.service", tgt=minion.id)
    if not ret.data:
        pytest.skip("Return daata is empty, skipping.")
    gen_sls = ret.data["Generated SLS file locations"][0]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert "service.running" in data[list(data.keys())[0]]
    assert ret.returncode == 0
