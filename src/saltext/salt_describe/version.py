# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pathlib
import os

version_file = pathlib.Path("version.txt").resolve()
print(version_file)
if version_file.exists():
    with open(version_file) as vfh:
        __version__ = vfh.read().strip()
        os.environ["SETUPTOOLS_SCM_PRETEND_VERSION"] = __version__
