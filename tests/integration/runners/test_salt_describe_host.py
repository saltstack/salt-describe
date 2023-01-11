# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import yaml


def test_host(salt_run_cli, minion):
    """
    Test describe.host
    """
    ret = salt_run_cli.run("describe.host", tgt=minion.id)
    gen_sls = ret.data["Generated SLS file locations"][0]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert "ip" in data["host_file_content_0"]["host.present"][0]
    assert ret.returncode == 0
