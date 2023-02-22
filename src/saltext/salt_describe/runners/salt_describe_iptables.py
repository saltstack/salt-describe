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


def iptables(tgt, tgt_type="glob", config_system="salt"):
    """
    Gather the iptable rules for minions and generate a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.iptables minion-tgt
    """
    mod_name = sys._getframe().f_code.co_name
    log.info("Attempting to generate SLS file for %s", mod_name)
    rules = __salt__["salt.execute"](
        tgt,
        "iptables.get_rules",
        tgt_type=tgt_type,
    )
    sls_files = []
    if not parse_salt_ret(ret=rules, tgt=tgt):
        return ret_info(sls_files, mod=mod_name)

    for minion in list(rules.keys()):
        state_contents = {}
        state_func = "iptables.append"

        rule = rules[minion]
        for table in list(rule):
            chains = list(rule[table])
            count = 0
            for chain in chains:

                _rules = rule[table][chain]["rules"]
                if not _rules:
                    continue
                for _rule in _rules:
                    kwargs = [{"chain": chain}, {"table": table}]
                    state_id = f"add_iptables_rule_{count}"
                    state_contents[state_id] = {state_func: []}
                    for kwarg in list(_rule.keys()):
                        kwargs.append({kwarg.replace("_", "-"): " ".join(_rule[kwarg])})
                    state_contents[state_id][state_func] = kwargs
                    count += 1

        state = yaml.dump(state_contents)

        sls_files.append(
            str(
                generate_files(
                    __opts__, minion, state, sls_name="iptables", config_system=config_system
                )
            )
        )

    return ret_info(sls_files, mod=mod_name)
