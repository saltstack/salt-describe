# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
def _parse_salt(minion, pip_list, **kwargs):
    """
    Parse the returned pip commands and return
    salt data.
    """

    state_name = "installed_pip_libraries"
    state_fun = "pip.installed"

    state_contents = {state_name: {state_fun: [{"pkgs": pip_list}]}}
    return state_contents


def _parse_ansible(minion, pip_list, **kwargs):
    """
    Parse the returned pip commands and return
    ansible data.
    """
    state_contents = []
    data = {"tasks": []}
    if not kwargs.get("hosts"):
        log.error(
            "Hosts was not passed. You will need to manually edit the playbook with the hosts entry"
        )
    else:
        data["hosts"] = kwargs.get("hosts")
    data["tasks"].append(
        {
            "name": f"installed_pip_libraries",
            "ansible.builtin.pip": {
                "name": pip_list,
            },
        }
    )
    state_contents.append(data)
    return state_contents
