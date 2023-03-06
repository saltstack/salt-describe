# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pytest
import yaml


def test_pkg(salt_run_cli, minion):
    """
    Test describe.pkg
    """
    ret = salt_run_cli.run("describe.pkg", tgt=minion.id)
    gen_sls = ret.data["Generated SLS file locations"][0]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    pkg_data = data["installed_packages"]["pkg.installed"][0]["pkgs"][0]
    assert isinstance(pkg_data, dict)
    assert ret.returncode == 0
