# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest
import yaml


@pytest.mark.skip_if_binaries_missing("iptables")
def test_iptables(salt_run_cli, minion):
    """
    Test describe.iptables
    """
    # Add one rule to ensure something in the state file
    ret = salt_run_cli.run(
        "iptables.append",
        table="filter=",
        chain="INPUT",
        rule="-m state --state RELATED,ESTABLISHED -j ACCEPT",
        tgt=minion.id,
    )

    ret = salt_run_cli.run("describe.iptables", tgt=minion.id)
    gen_sls = ret.data["Generated SLS file locations"][0]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    if not data:
        pytest.skip("State file contents is empty, no iptables rules available.  Skipping")
    assert "chain" in data["add_iptables_rule_0"]["iptables.append"][0]
    assert ret.returncode == 0
