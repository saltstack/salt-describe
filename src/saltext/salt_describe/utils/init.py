import saltext.salt_describe.utils.salt_describe


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
