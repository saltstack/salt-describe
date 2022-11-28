import pathlib

import salt.config
import salt.syspaths
import salt.utils.files
import yaml


def generate_files(opts, minion, state, sls_name="default", env="base"):
    """
    Generate an sls file for the minion with given state contents
    """
    minion_state_root = pathlib.Path("/srv", "ansible")
    minion_state_root.mkdir(parents=True, exist_ok=True)

    minion_state_file = minion_state_root / f"{sls_name}.yml"

    with salt.utils.files.fopen(minion_state_file, "w") as fp_:
        fp_.write(state)

    return True
