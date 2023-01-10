# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import yaml


def test_timezone(salt_run_cli, minion):
    """
    Test describe.timezone
    """
    ret = salt_run_cli.run("describe.timezone", tgt=minion.id)
    gen_sls = ret.data["Generated SLS file locations"][0]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert "timezone.system" in data[list(data.keys())[0]]
    assert ret.returncode == 0
