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


__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def _parse_salt(minion, service_status, enabled_services, disabled_services, **kwargs):
    """
    Parse the returned service commands and return
    salt data.
    """
    _services = service_status[minion]
    state_contents = {}
    for service, status in _services.items():
        state_name = f"{service}"
        _enabled = service in enabled_services.get(minion)
        _disabled = service in disabled_services.get(minion)

        if status:
            service_function = "service.running"
        else:
            service_function = "service.dead"

        if _enabled:
            state_contents[state_name] = {service_function: [{"enable": True}]}
        elif _disabled:
            state_contents[state_name] = {service_function: [{"enable": False}]}
        else:
            state_contents[state_name] = {service_function: []}
    return state_contents


def _parse_ansible(minion, service_status, enabled_services, disabled_services, **kwargs):
    """
    Parse the returned service commands and return
    ansible data.
    """
    _services = service_status[minion]
    data = {"name": "Manage Service", "tasks": []}
    if not kwargs.get("hosts"):
        log.error(
            "Hosts was not passed. You will need to manually edit the playbook with the hosts entry"
        )
    else:
        data["hosts"] = kwargs.get("hosts")
    state_contents = []

    for service, status in _services.items():
        if "@" in service:
            continue
        state_name = f"{service}"
        _enabled = service in enabled_services.get(minion)
        _disabled = service in disabled_services.get(minion)

        if status:
            service_function = "started"
        else:
            service_function = "stopped"

        if _enabled:
            data["tasks"].append(
                {
                    "name": f"Manage service {service}",
                    "service": {
                        "state": service_function,
                        "name": service,
                        "enabled": "yes",
                    },
                }
            )
        elif _disabled:
            data["tasks"].append(
                {
                    "name": f"Manage service {service}",
                    "service": {
                        "state": service_function,
                        "name": service,
                        "enabled": "no",
                    },
                }
            )
    state_contents.append(data)
    return state_contents


def _parse_chef(minion, service_status, enabled_services, disabled_services, **kwargs):
    """
    Parse the returned service commands and return
    chef data.
    """

    _services = service_status[minion]
    _contents = []
    for service, status in _services.items():
        _enabled = service in enabled_services.get(minion)
        _disabled = service in disabled_services.get(minion)

        actions = []
        if _enabled:
            actions.append(":enable")
        elif _disabled:
            actions.append(":disable")

        if status:
            actions.append(":start")
        else:
            actions.append(":stop")

        _actions = ", ".join(actions)
        service_template = f"""service '{service}' do
  action [ {_actions} ]
end
"""
        _contents.append(service_template)
    return _contents


def service(tgt, tgt_type="glob", config_system="salt", **kwargs):
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
    enabled_services = __salt__["salt.execute"](
        tgt,
        "service.get_enabled",
        tgt_type=tgt_type,
    )
    disabled_services = __salt__["salt.execute"](
        tgt,
        "service.get_disabled",
        tgt_type=tgt_type,
    )

    if sys.platform.startswith("darwin"):

        all_services = __salt__["salt.execute"](
            tgt,
            "service.list",
            tgt_type=tgt_type,
        )
        buf = io.StringIO(all_services[tgt])
        contents = buf.readlines()

        service_status = {tgt: {}}
        for _line in contents:
            if "PID" in _line:
                continue
            pid, status, service = _line.split()
            if pid == "-":
                service_status[tgt][service] = False
            else:
                service_status[tgt][service] = True
        func_ret = [service_status, enabled_services]
    else:
        service_status = __salt__["salt.execute"](
            tgt,
            "service.status",
            "*",
            tgt_type=tgt_type,
        )
        func_ret = [service_status, disabled_services, enabled_services]

    sls_files = []
    for _func_ret in func_ret:
        if not parse_salt_ret(ret=_func_ret, tgt=tgt):
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
            str(
                generate_files(
                    __opts__, minion, state, sls_name="service", config_system=config_system
                )
            )
        )

    return ret_info(sls_files, mod=mod_name)
