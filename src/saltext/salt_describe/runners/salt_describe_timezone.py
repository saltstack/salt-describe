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


def timezone(tgt, tgt_type="glob"):
    """
    Gather the timezone data for minions and generate a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.timezone minion-tgt

    """

    timezones = __salt__["salt.execute"](
        tgt,
        "timezone.get_zone",
        tgt_type=tgt_type,
    )

    for minion in list(timezones.keys()):
        timezone = timezones[minion]

        state_contents = {}
        state_contents = {timezone: {"timezone.system": []}}

        state = yaml.dump(state_contents)

        generate_sls(__opts__, minion, state, sls_name="timezone")

    return True
