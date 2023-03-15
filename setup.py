# pylint: disable=missing-module-docstring
import os
import pathlib

import setuptools

if __name__ == "__main__":
    version_file = pathlib.Path("version.txt").resolve()
    if version_file.exists():
        with open(version_file) as vfh:
            os.environ["SETUPTOOLS_SCM_PRETEND_VERSION"] = vfh.read().strip()

    setuptools.setup(use_scm_version=True)
