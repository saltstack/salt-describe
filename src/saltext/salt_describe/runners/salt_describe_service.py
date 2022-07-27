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


def service(tgt, tgt_type="glob"):
    """
    Gather enabled and disabled services on minions and build a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.service minion-tgt

    """

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

    service_status = __salt__["salt.execute"](
        tgt,
        "service.status",
        "*",
        tgt_type=tgt_type,
    )

    for minion in list(service_status.keys()):
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

        state = yaml.dump(state_contents)
        generate_sls(__opts__, minion, state, "services")

    return True
