# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Module for building state file

.. versionadded:: 3006

"""
import logging
import sys

import yaml
from saltext.salt_describe.utils.init import generate_files
from saltext.salt_describe.utils.init import parse_salt_ret
from saltext.salt_describe.utils.init import ret_info

__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def host(tgt, tgt_type="glob", config_system="salt"):
    """
    Gather /etc/hosts file content on minions and build a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.host minion-tgt

    """
    mod_name = sys._getframe().f_code.co_name
    log.info("Attempting to generate SLS file for %s", mod_name)
    ret = __salt__["salt.execute"](
        tgt,
        "hosts.list_hosts",
        tgt_type=tgt_type,
    )
    sls_files = []
    if not parse_salt_ret(ret=ret, tgt=tgt):
        return ret_info(sls_files, mod=mod_name)

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
        sls_files.append(
            str(
                generate_files(
                    __opts__, minion, state, sls_name="host", config_system=config_system
                )
            )
        )

    return ret_info(sls_files, mod=mod_name)
