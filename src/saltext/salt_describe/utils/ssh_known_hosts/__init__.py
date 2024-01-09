# Copyright 2023-2024 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
import logging

log = logging.getLogger(__name__)


def _parse_salt(minion, user_keys, **kwargs):
    """
    Parse the returned ssh_known_hosts commands and return
    salt data.
    """
    state_contents = {}
    for user in user_keys:
        for key in user_keys[user]:
            data = user_keys[user][key]
            ssh_auth_present = [{"user": user}, {"enc": data["enc"]}]

            if data.get("options"):
                ssh_auth_present.append({"options": data["options"]})
            if data.get("comment"):
                ssh_auth_present.append({"comment": data["comment"]})

            state_contents[key] = {"ssh_auth.present": ssh_auth_present}

    return state_contents
