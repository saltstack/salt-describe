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


def iptables(tgt, tgt_type="glob"):
    """
    Gather the iptable rules for minions and generate a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.iptables minion-tgt
    """
    rules = __salt__["salt.execute"](
        tgt,
        "iptables.get_rules",
        tgt_type=tgt_type,
    )
    for minion in list(rules.keys()):
        state_contents = {}
        state_func = "iptables.append"

        rule = rules[minion]
        table = list(rule)[0]
        chains = list(rule[table])
        count = 0
        for chain in chains:

            _rules = rule[table][chain]["rules"]
            if not _rules:
                break
            for _rule in _rules:
                kwargs = [{"chain": chain}, {"table": table}]
                state_id = f"add_iptables_rule_{count}"
                state_contents[state_id] = {state_func: []}
                for kwarg in list(_rule.keys()):
                    kwargs.append({kwarg.replace("_", "-"): " ".join(_rule[kwarg])})
                state_contents[state_id][state_func] = kwargs
                count += 1

        state = yaml.dump(state_contents)

        generate_sls(__opts__, minion, state, sls_name="iptables")

    return True
