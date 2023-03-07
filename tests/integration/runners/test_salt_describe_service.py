# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import sys

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

    if sys.platform.startswith("win"):
        _service = "Schedule"
    elif sys.platform.startswith("darwin"):
        _service = "com.apple.homed"
    else:
        _service = "sshd"
    assert _service in data
    assert "service.running" in data[_service]
    assert ret.returncode == 0
