# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import MagicMock
from unittest.mock import patch

import saltext.salt_describe.utils.ansible_describe as ansible_describe_util
import yaml


def test_generate_files(tmp_path):
    yml_contents = [
        {
            "tasks": [
                {
                    "ansible.builtin.service": {"state": "started", "name": "apache2"},
                    "name": "Start service apache",
                }
            ],
            "hosts": "localhost",
            "name": "Manage Service",
        }
    ]

    yml = yaml.dump(yml_contents)
    root = tmp_path / "ansible" / "minion"
    assert (
        ansible_describe_util.generate_files(
            {}, "minion", yml, sls_name="file", env="prod", root=tmp_path
        )
        is True
    )
    yml_file = root / "file.yml"
    assert yml_file.exists()
    assert yaml.safe_load(yml_file.read_text()) == yml_contents
