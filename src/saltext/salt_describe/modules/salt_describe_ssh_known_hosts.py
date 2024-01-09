# Copyright 2023-2024 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Module for building state file

.. versionadded:: 1.1.0

"""
import logging
import sys

import salt.utils.minions  # pylint: disable=import-error
import yaml
from saltext.salt_describe.utils.init import generate_files
from saltext.salt_describe.utils.init import parse_salt_ret
from saltext.salt_describe.utils.init import ret_info
from saltext.salt_describe.utils.ssh_known_hosts import _parse_salt


__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def ssh_known_hosts(config_system="salt", user=None, **kwargs):
    """
    Gather installed ssh_known_hosts on minions and build a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.ssh_known_hosts

        salt-run describe.ssh_known_hosts config_system=ansible

        salt-run describe.ssh_known_hosts config_system=chef
    """
    ret = {}
    mod_name = sys._getframe().f_code.co_name
    log.info("Attempting to generate SLS file for %s", mod_name)
    minion = __salt__["config.get"]("id")
    ret[minion] = __salt__["ssh.auth_keys"](user=user)

    sls_files = []
    if not parse_salt_ret(ret=ret, tgt=minion):
        return ret_info(sls_files, mod=mod_name)

    _, grains, _ = salt.utils.minions.get_minion_data(minion, __opts__)

    known_hosts = ret[minion]
    state_contents = getattr(sys.modules[__name__], f"_parse_{config_system}")(
        minion, known_hosts, **kwargs
    )

    if config_system in ("ansible", "salt"):
        state = yaml.dump(state_contents)
    else:
        state = "\n".join(state_contents)

    sls_files.append(
        generate_files(
            __opts__, minion, state, sls_name="ssh_known_hosts", config_system=config_system
        )
    )

    return ret_info(sls_files, mod=mod_name)
