# pylint: disable=missing-module-docstring
import setuptools

import src.saltext.salt_describe.version as describe_version


if __name__ == "__main__":
    setuptools.setup(use_scm_version=True)
