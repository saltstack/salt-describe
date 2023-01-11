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


def sysctl(tgt, sysctl_items, tgt_type="glob", config_system="salt"):
    """
    read sysctl on the minions and build a state file
    to managed the sysctl settings.

    CLI Example:

    .. code-block:: bash

        salt-run describe.sysctl minion-tgt '[vm.swappiness,vm.dirty_ratio]'
    """
    mod_name = sys._getframe().f_code.co_name
    log.info("Attempting to generate SLS file for %s", mod_name)
    sysctls = __salt__["salt.execute"](
        tgt,
        "sysctl.show",
        tgt_type=tgt_type,
    )

    state_contents = {}
    sls_files = []
    if not parse_salt_ret(ret=sysctls, tgt=tgt):
        return ret_info(sls_files, mod=mod_name)

    for minion in list(sysctls.keys()):
        for current in sysctl_items:
            if current in sysctls[minion].keys():
                payload = [{"name": current}, {"value": sysctls[minion][current]}]
                state_contents[f"sysctl-{current}"] = {"sysctl.present": payload}
            else:
                log.error("%s not found in sysctl", current)

        state = yaml.dump(state_contents)
        sls_files.append(
            str(
                generate_files(
                    __opts__, minion, state, sls_name="sysctl", config_system=config_system
                )
            )
        )

    return ret_info(sls_files, mod=mod_name)
