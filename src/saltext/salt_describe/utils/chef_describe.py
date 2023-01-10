# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pathlib

import salt.config
import salt.syspaths
import salt.utils.files
import yaml


def generate_files(opts, minion, state, sls_name="default", env="base", root=None):
    """
    Generate an sls file for the minion with given state contents
    """
    if not root:
        minion_state_root = pathlib.Path("/srv", "chef", minion)
    else:
        minion_state_root = pathlib.Path(root, "chef", minion)
    minion_state_root.mkdir(parents=True, exist_ok=True)

    minion_state_file = minion_state_root / f"{sls_name}.rb"

    with salt.utils.files.fopen(minion_state_file, "w") as fp_:
        fp_.write(state)

    return True
