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


def firewalld(tgt, tgt_type="glob", config_system="salt"):
    """
    Gather the firewalld rules for minions and generate a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.firewalld minion-tgt
    """
    rules = __salt__["salt.execute"](
        tgt,
        "firewalld.list_all",
        tgt_type=tgt_type,
    )
    for minion in list(rules.keys()):
        state_contents = {}
        state_func = "firewalld.present"

        rule = rules[minion]
        zones = rule.keys()
        count = 0
        for zone in zones:
            state_id = f"add_firewalld_rule_{count}"
            state_contents[state_id] = {state_func: []}
            kwargs = [
                x
                for x in (
                    {"name": zone},
                    {"block_icmp": rule[zone]["icmp-blocks"]},
                    {"ports": rule[zone]["ports"]},
                    {"port_fwd": rule[zone]["forward-ports"]},
                    {"services": rule[zone]["services"][0].split()},
                    {"interfaces": rule[zone]["interfaces"]},
                    {"sources": rule[zone]["sources"]},
                    {"rich_rules": rule[zone]["rich rules"]},
                )
                if not list(x.values()) == [[""]] or not list(x.values())
            ]
            if rule[zone]["target"] == "default":
                kwargs["default"] = True
            if rule[zone]["masquerade"] == "yes":
                kwargs["masquerade"] = True

            state_contents[state_id][state_func] = kwargs
            count += 1

        state = yaml.dump(state_contents)

        generate_files(__opts__, minion, state, sls_name="firewalld", config_system=config_system)

    return True
