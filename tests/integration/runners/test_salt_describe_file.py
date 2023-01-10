# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import yaml


def test_file(salt_run_cli, minion, tmp_path):
    """
    Test describe.file
    """
    test_file = tmp_path / "testme"
    test_data = "Success!"
    with open(test_file, "w") as fp:
        fp.write(test_data)

    ret = salt_run_cli.run("describe.file", tgt=minion.id, paths=[str(test_file)])

    gen_sls = ret.data["Generated SLS file locations"][0]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert (
        data[str(test_file)]["file.managed"][0]["source"] == f"salt://{minion.id}/files/{test_file}"
    )
    assert ret.returncode == 0
