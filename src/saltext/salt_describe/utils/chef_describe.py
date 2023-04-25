# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging
import pathlib

import salt.config
import salt.syspaths
import salt.utils.files
import yaml

log = logging.getLogger(__name__)


def generate_files(opts, minion, state, sls_name="default", env="base", root=None):
    """
    Generate an sls file for the minion with given state contents
    """
    if not root:
        minion_state_root = pathlib.Path("/srv", "chef", minion)
    else:
        minion_state_root = pathlib.Path(root, "chef", minion)
    try:
        minion_state_root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        log.warning(
            f"Unable to create directory {str(minion_state_root)}.  Check that the salt user has the correct permissions."
        )
        return False

    minion_state_file = minion_state_root / f"{sls_name}.rb"

    with salt.utils.files.fopen(minion_state_file, "w") as fp_:
        fp_.write(state)

    return minion_state_file
