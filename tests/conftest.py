# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from saltext.salt_describe import PACKAGE_ROOT
from saltfactories.utils import random_string


@pytest.fixture(scope="session")
def salt_factories_config():
    """
    Return a dictionary with the keyworkd arguments for FactoriesManager
    """
    return {
        "code_dir": str(PACKAGE_ROOT),
        "start_timeout": 120 if os.environ.get("CI") else 60,
    }


@pytest.fixture(scope="package")
def master(salt_factories, base_env_state_tree_root_dir):
    config_defaults = {
        "file_roots": {
            "base": [
                str(base_env_state_tree_root_dir),
            ]
        },
        "enable_fqdns_grains": False,
        "timeout": 120,
    }

    return salt_factories.salt_master_daemon(random_string("master-"), defaults=config_defaults)


@pytest.fixture(scope="package")
def minion(master):
    config_defaults = {"enable_fqdns_grains": False, "timeout": 120}
    return master.salt_minion_daemon(random_string("minion-"), defaults=config_defaults)


@pytest.fixture(scope="session")
def integration_files_dir(salt_factories):
    """
    Fixture which returns the salt integration files directory path.
    Creates the directory if it does not yet exist.
    """
    dirname = salt_factories.root_dir / "integration-files"
    dirname.mkdir(exist_ok=True)
    return dirname


@pytest.fixture(scope="session")
def state_tree_root_dir(integration_files_dir):
    """
    Fixture which returns the salt state tree root directory path.
    Creates the directory if it does not yet exist.
    """
    dirname = integration_files_dir / "state-tree"
    dirname.mkdir(exist_ok=True)
    return dirname


@pytest.fixture(scope="session")
def base_env_state_tree_root_dir(state_tree_root_dir):
    """
    Fixture which returns the salt base environment state tree directory path.
    Creates the directory if it does not yet exist.
    """
    dirname = state_tree_root_dir / "base"
    dirname.mkdir(exist_ok=True)
    return dirname
