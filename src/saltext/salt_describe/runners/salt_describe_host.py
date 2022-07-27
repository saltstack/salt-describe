"""
Module for building state file

.. versionadded:: 3006

"""
import logging

import yaml
from saltext.salt_describe.utils.salt_describe import generate_sls

__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def host(tgt, tgt_type="glob"):
    """
    Gather /etc/hosts file content on minions and build a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.host minion-tgt

    """
    ret = __salt__["salt.execute"](
        tgt,
        "hosts.list_hosts",
        tgt_type=tgt_type,
    )

    for minion in list(ret.keys()):
        content = ret[minion]
        count = 0
        state_contents = {}
        for key, value in content.items():
            sls_id = f"host_file_content_{count}"
            state_func = "host.present"
            if key.startswith("comment"):
                pass
            else:
                state_contents[sls_id] = {state_func: [{"ip": []}, {"names": []}]}
                state_contents[sls_id][state_func][0]["ip"] = key
                state_contents[sls_id][state_func][1]["names"] = value["aliases"]
                count += 1

        state = yaml.dump(state_contents)
        generate_sls(__opts__, minion, state, "host")

    return True
