# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import yaml


def test_top(salt_run_cli, minion, base_env_state_tree_root_dir):
    """
    Test describe.top. Multiple scenarios tested:
        - When top.sls does not exist. Ensure top.sls
        is generated correctly with data.
        - When describe.top is called again when no other
        SLS file has been added
        - When describe.top is called after another SLS file
        has been added.
    """
    # First create a SLS file with describe
    ret = salt_run_cli.run("describe.host", tgt=minion.id)
    assert ret.returncode == 0
    # Now generate the top data with the SLS data
    ret = salt_run_cli.run("describe.top", tgt=minion.id)
    assert ret.returncode == 0
    gen_sls = ret.data["Generated SLS file locations"]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert data["base"][minion.id] == [f"{minion.id}.host"]

    # Run describe.top and ensure it doesn't add any other entires
    ret = salt_run_cli.run("describe.top", tgt=minion.id)
    assert ret.returncode == 0
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert data["base"][minion.id] == [f"{minion.id}.host"]
    assert len(data["base"][minion.id]) == 1

    # Now add another SLS file and then run top again to ensure it adds it
    ret = salt_run_cli.run("describe.pkg", tgt=minion.id)
    assert ret.returncode == 0
    ret = salt_run_cli.run("describe.top", tgt=minion.id)
    assert ret.returncode == 0
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert data["base"][minion.id] == [f"{minion.id}.host", f"{minion.id}.pkg"]
    assert len(data["base"][minion.id]) == 2
