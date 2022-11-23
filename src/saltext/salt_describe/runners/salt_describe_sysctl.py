"""
Module for building state file

.. versionadded:: 3006

"""
import logging

import yaml
from saltext.salt_describe.utils.init import generate_files

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
    sysctls = __salt__["salt.execute"](
        tgt,
        "sysctl.show",
        tgt_type=tgt_type,
    )

    state_contents = {}
    for minion in list(sysctls.keys()):
        for current in sysctl_items:
            if current in sysctls[minion].keys():
                payload = [{"name": current}, {"value": sysctls[minion][current]}]
                state_contents[f"sysctl-{current}"] = {"sysctl.present": payload}
            else:
                log.error("%s not found in sysctl", current)

        state = yaml.dump(state_contents)
        generate_files(__opts__, minion, state, sls_name="sysctl", config_system=config_system)

    return True
