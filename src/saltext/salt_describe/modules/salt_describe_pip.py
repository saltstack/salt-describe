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
from saltext.salt_describe.utils.pip import _parse_ansible
from saltext.salt_describe.utils.pip import _parse_salt

__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def pip(bin_env=None, config_system="salt", **kwargs):
    """
    Gather installed pip libraries and build a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.pip minion-tgt

    """
    mod_name = sys._getframe().f_code.co_name
    log.info("Attempting to generate SLS file for %s", mod_name)
    minion_id = __salt__["config.get"]("id")
    ret = {minion_id: __salt__["pip.freeze"](bin_env=bin_env)}
    if not parse_salt_ret(ret=ret, tgt=minion_id):
        return ret_info(sls_files, mod=mod_name)

    sls_files = []
    for minion in list(ret.keys()):
        minion_pip_list = ret[minion]
        state_contents = getattr(sys.modules[__name__], f"_parse_{config_system}")(
            minion, minion_pip_list, **kwargs
        )
        state = yaml.dump(state_contents)

        sls_files.append(
            generate_files(__opts__, minion, state, sls_name="pip", config_system=config_system)
        )

    return ret_info(sls_files, mod=mod_name)
