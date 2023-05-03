# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0


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
