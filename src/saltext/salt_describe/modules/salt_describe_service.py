# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Module for building state file

.. versionadded:: 3006

"""
import io
import logging
import sys

import yaml
from saltext.salt_describe.utils.init import generate_files
from saltext.salt_describe.utils.init import parse_salt_ret
from saltext.salt_describe.utils.init import ret_info
from saltext.salt_describe.utils.service import _parse_ansible
from saltext.salt_describe.utils.service import _parse_chef
from saltext.salt_describe.utils.service import _parse_salt


__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def service(config_system="salt", **kwargs):
    """
    Gather enabled and disabled services on minions and build a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.service minion-tgt

    If you want to generate ansible playbooks you need to pass in
    `config_system` and `hosts`

    .. code-block:: bash

        salt-run describe.service minion-tgt config_system=ansible hosts=hostgroup
    """
    mod_name = sys._getframe().f_code.co_name
    log.info("Attempting to generate SLS file for %s", mod_name)
    minion_id = __salt__["config.get"]("id")
    enabled_services = {minion_id: __salt__["service.get_enabled"]()}
    disabled_services = {minion_id: __salt__["service.get_disabled"]()}

    if sys.platform.startswith("darwin"):

        all_services = {minion_id: __salt__["service.list"]()}
        buf = io.StringIO(all_services[minion_id])
        contents = buf.readlines()

        service_status = {minion_id: {}}
        for _line in contents:
            if "PID" in _line:
                continue
            pid, status, service = _line.split()
            if pid == "-":
                service_status[minion_id][service] = False
            else:
                service_status[minion_id][service] = True
        func_ret = [service_status, enabled_services]
    else:
        service_status = {minion_id: __salt__["service.status"]("*")}
        func_ret = [service_status, disabled_services, enabled_services]

    sls_files = []
    for _func_ret in func_ret:
        if not parse_salt_ret(ret=_func_ret, tgt=minion_id):
            return ret_info(sls_files, mod=mod_name)

    for minion in list(service_status.keys()):
        state_contents = getattr(sys.modules[__name__], f"_parse_{config_system}")(
            minion, service_status, enabled_services, disabled_services, **kwargs
        )
        if config_system in ("ansible", "salt"):
            state = yaml.dump(state_contents)
        else:
            state = "\n".join(state_contents)
        sls_files.append(
            generate_files(__opts__, minion, state, sls_name="service", config_system=config_system)
        )

    return ret_info(sls_files, mod=mod_name)
