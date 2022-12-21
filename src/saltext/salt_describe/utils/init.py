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


def ret_info(sls_files):
    if not sls_files:
        log.error("SLS file not generated")
        return False
    return {"Generated SLS file locations": sls_files}
