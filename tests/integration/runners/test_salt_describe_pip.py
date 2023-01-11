# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import yaml


def test_pip(salt_run_cli, minion):
    """
    Test describe.pip
    """
    ret = salt_run_cli.run("describe.pip", tgt=minion.id)
    gen_sls = ret.data["Generated SLS file locations"][0]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert "pkgs" in data["installed_pip_libraries"]["pip.installed"][0]
    assert ret.returncode == 0
