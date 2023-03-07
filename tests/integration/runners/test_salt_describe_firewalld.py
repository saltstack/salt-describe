# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest
import yaml


@pytest.mark.skip_if_binaries_missing("firewall-cmd")
def test_firewalld(salt_run_cli, minion):
    """
    Test describe.firewalld
    """
    ret = salt_run_cli.run("describe.firewalld", tgt=minion.id)
    gen_sls = ret.data["Generated SLS file locations"][0]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert "name" in data["add_firewalld_rule_0"]["firewalld.present"][0]
    assert ret.returncode == 0
