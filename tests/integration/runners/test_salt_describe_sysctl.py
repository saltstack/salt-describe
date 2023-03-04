# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import sys

import pytest
import yaml


@pytest.mark.skip_if_binaries_missing("sysctl")
def test_sysctl(salt_run_cli, minion):
    """
    Test describe.sysctl
    """
    if sys.platform.startswith("darwin"):
        sysctl_key = "vm.swapusage"
    else:
        sysctl_key = "vm.swappiness"
    ret = salt_run_cli.run("describe.sysctl", tgt=minion.id, sysctl_items=[sysctl_key])
    gen_sls = ret.data["Generated SLS file locations"][0]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert data[f"sysctl-{sysctl_key}"]["sysctl.present"][0]["name"] == sysctl_key
    assert ret.returncode == 0
