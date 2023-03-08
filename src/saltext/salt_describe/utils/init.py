# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging

import saltext.salt_describe.utils.ansible_describe
import saltext.salt_describe.utils.chef_describe
import saltext.salt_describe.utils.salt_describe


log = logging.getLogger(__name__)


def generate_files(opts, minion, state, sls_name="default", env="base", config_system="salt"):
    """
    Generate the files for the given config management system
    """
    config = getattr(saltext.salt_describe.utils, f"{config_system}_describe")

    return config.generate_files(opts, minion, state, sls_name=sls_name, env=env)


def get_minion_state_file_root(opts, minion, env="base", config_system="salt"):
    """
    Return the state file root for the given minion
    """
    config = getattr(saltext.salt_describe.utils, f"{config_system}_describe")

    return config.get_minion_state_file_root(opts, minion, env=env)


def ret_info(sls_files, mod=None):
    if not sls_files:
        if mod:
            log.error("Could not generate SLS file for %s", mod)
        return False
    return {"Generated SLS file locations": sls_files}


def parse_salt_ret(ret, tgt):
    """
    Parse the Salt return to check for Success
    or Error
    """
    _status = []
    _errorrs = [
        "ERROR:",
        "is not available",
        "module cannot be loaded",
        "__virtual__ returned False",
    ]
    for _tgt in ret:
        for _error in _errorrs:
            if _error in ret[_tgt]:
                log.error(ret)
                _status.append(False)
        _status.append(True)
    return all(_status)
