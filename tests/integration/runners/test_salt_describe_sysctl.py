import yaml


def test_sysctl(salt_run_cli, minion):
    """
    Test describe.sysctl
    """
    ret = salt_run_cli.run("describe.sysctl", tgt=minion.id, sysctl_items=["vm.swappiness"])
    gen_sls = ret.data["Generated SLS file locations"][0]
    with open(gen_sls) as fp:
        data = yaml.safe_load(fp)
    assert data["sysctl-vm.swappiness"]["sysctl.present"][0]["name"] == "vm.swappiness"
    assert ret.returncode == 0
