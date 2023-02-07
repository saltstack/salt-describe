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
from saltext.salt_describe.utils.salt_describe import generate_pillars

__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def user(tgt, require_groups=False, tgt_type="glob", config_system="salt"):
    """
    read users on the minions and build a state file
    to manage the users.

    CLI Example:

    .. code-block:: bash

        salt-run describe.user minion-tgt
    """
    mod_name = sys._getframe().f_code.co_name
    log.info("Attempting to generate SLS file for %s", mod_name)
    state_contents = {}
    if require_groups is True:
        __salt__["describe.group"](tgt=tgt, include_members=False, tgt_type=tgt_type)

    users = __salt__["salt.execute"](
        tgt,
        "user.getent",
        tgt_type=tgt_type,
    )

    pillars = {"users": {}}
    sls_files = []
    if not parse_salt_ret(ret=users, tgt=tgt):
        return ret_info(sls_files, mod=mod_name)

    for minion in list(users.keys()):
        for user in users[minion]:
            shadow = __salt__["salt.execute"](
                minion, "shadow.info", arg=[user["name"]], tgt_type="glob"
            )[minion]

            homeexists = __salt__["salt.execute"](
                minion, "file.directory_exists", arg=[user["home"]], tgt_type="glob"
            )[minion]
            username = user["name"]
            payload = [
                {"name": username},
                {"uid": user["uid"]},
                {"gid": user["gid"]},
                {"allow_uid_change": True},
                {"allow_gid_change": True},
                {"home": user["home"]},
                {"shell": user["shell"]},
                {"groups": user["groups"]},
                {"password": f'{{{{ salt["pillar.get"]("users:{username}","*") }}}}'},
                {"enforce_password": True},
                {"date": shadow["lstchg"]},
                {"mindays": shadow["min"]},
                {"maxdays": shadow["max"]},
                {"inactdays": shadow["inact"]},
                {"expire": shadow["expire"]},
            ]
            if homeexists:
                payload.append({"createhome": True})
            else:
                payload.append({"createhome": False})
            # GECOS
            if user["fullname"]:
                payload.append({"fullname": user["fullname"]})
            if user["homephone"]:
                payload.append({"homephone": user["homephone"]})
            if user["other"]:
                payload.append({"other": user["other"]})
            if user["roomnumber"]:
                payload.append({"roomnumber": user["roomnumber"]})
            if user["workphone"]:
                payload.append({"workphone": user["workphone"]})

            state_contents[f"user-{username}"] = {"user.present": payload}
            passwd = shadow["passwd"]
            if passwd != "*":
                pillars["users"].update({user["name"]: f"{passwd}"})

        state = yaml.dump(state_contents)
        pillars = yaml.dump(pillars)
        sls_files.append(
            str(
                generate_files(
                    __opts__, minion, state, sls_name="users", config_system=config_system
                )
            )
        )
        generate_pillars(__opts__, minion, pillars, sls_name="users")
    return ret_info(sls_files, mod=mod_name)


def group(tgt, include_members=False, tgt_type="glob", config_system="salt"):
    """
    read groups on the minions and build a state file
    to managed th groups.

    CLI Example:

    .. code-block:: bash

        salt-run describe.group minion-tgt
    """
    mod_name = sys._getframe().f_code.co_name
    groups = __salt__["salt.execute"](
        tgt,
        "group.getent",
        tgt_type=tgt_type,
    )
    if not parse_salt_ret(ret=groups, tgt=tgt):
        return ret_info(sls_files, mod=mod_name)

    state_contents = {}
    sls_files = []
    for minion in list(groups.keys()):
        for group in groups[minion]:
            groupname = group["name"]
            payload = [{"name": groupname}, {"gid": group["gid"]}]
            if include_members is True:
                payload.append({"members": group["members"]})
            state_contents[f"group-{groupname}"] = {"group.present": payload}

        state = yaml.dump(state_contents)

        sls_files.append(
            str(
                generate_files(
                    __opts__, minion, state, sls_name="groups", config_system=config_system
                )
            )
        )

    return ret_info(sls_files, mod=mod_name)
