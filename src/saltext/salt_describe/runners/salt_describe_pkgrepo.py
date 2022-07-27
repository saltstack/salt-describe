"""
Module for building state file

.. versionadded:: 3006

"""
import logging
import re

import salt.utils.minions  # pylint: disable=import-error
import yaml
from saltext.salt_describe.utils.salt_describe import generate_sls


__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def pkgrepo(tgt, tgt_type="glob"):
    """
    Gather the package repo data for minions and generate a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.pkgrepo minion-tgt

    """

    pkgrepos = __salt__["salt.execute"](
        tgt,
        "pkg.list_repos",
        tgt_type=tgt_type,
    )

    for minion in list(pkgrepos.keys()):
        _, grains, _ = salt.utils.minions.get_minion_data(minion, __opts__)

        if grains["os_family"] not in ("Debian", "RedHat"):
            log.debug("Unsupported minion")
            continue

        _pkgrepo = pkgrepos[minion]

        state_contents = {}
        state_name = f"{pkgrepo}"
        state_func = "pkgrepo.managed"

        for _pkgrepo_name in _pkgrepo:
            if isinstance(_pkgrepo[_pkgrepo_name], dict):

                if grains["os_family"] == "RedHat":
                    state_contents[_pkgrepo_name] = {
                        state_func: [
                            {"humanname": _pkgrepo[_pkgrepo_name]["name"]},
                            {"gpgkey": _pkgrepo[_pkgrepo_name]["gpgkey"]},
                            {"gpgcheck": _pkgrepo[_pkgrepo_name]["gpgcheck"]},
                            {"enabled": _pkgrepo[_pkgrepo_name]["enabled"]},
                        ]
                    }

                    if "metalink" in _pkgrepo[_pkgrepo_name]:
                        state_contents[_pkgrepo_name][state_func].append(
                            {"metalink": _pkgrepo[_pkgrepo_name]["metalink"]}
                        )
                    elif "baseurl" in _pkgrepo[_pkgrepo_name]:
                        state_contents[_pkgrepo_name][state_func].append(
                            {"baseurl": _pkgrepo[_pkgrepo_name]["baseurl"]}
                        )
                    elif "mirrorlist" in _pkgrepo[_pkgrepo_name]:
                        state_contents[_pkgrepo_name][state_func].append(
                            {"mirrorlist": _pkgrepo[_pkgrepo_name]["mirrorlist"]}
                        )

            elif isinstance(_pkgrepo[_pkgrepo_name], list):
                for item in _pkgrepo[_pkgrepo_name]:
                    if grains["os_family"] == "Debian":

                        sls_id = re.sub(r"^#\ ", "", item["line"])

                        state_contents[sls_id] = {
                            state_func: [
                                {"file": item["file"]},
                                {"dist": item["dist"]},
                                {"refresh": False},
                                {"disabled": item["disabled"]},
                            ]
                        }

                        if "comps" in item and item["comps"]:
                            comps = ",".join(item["comps"])
                            state_contents[sls_id][state_func].append({"comps": comps})

                        if "architectures" in item and item["architectures"]:
                            architectures = ",".join(item["architectures"])
                            state_contents[sls_id][state_func].append(
                                {"architectures": architectures}
                            )

        state = yaml.dump(state_contents)

        generate_sls(__opts__, minion, state, state_name)

    return True
