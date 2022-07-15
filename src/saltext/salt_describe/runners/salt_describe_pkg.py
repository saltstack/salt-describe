"""
Module for building state file

.. versionadded:: 3006

"""
import functools
import inspect
import logging
import os.path
import pathlib
import re
import sys
import re

import salt.daemons.masterapi
import salt.utils.files
import salt.utils.pkg.deb
import yaml

from saltext.salt_describe.utils.salt_describe import generate_sls

__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def pkg(tgt, tgt_type="glob", include_version=True, single_state=True):
    """
    Gather installed pkgs on minions and build a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.pkg minion-tgt

    """

    ret = __salt__["salt.execute"](
        tgt,
        "pkg.list_pkgs",
        tgt_type=tgt_type,
    )

    for minion in list(ret.keys()):
        _pkgs = ret[minion]
        if single_state:
            if include_version:
                pkgs = [{name: version} for name, version in _pkgs.items()]
            else:
                pkgs = list(_pkgs.keys())

            state_contents = {"installed_packages": {"pkg.installed": [{"pkgs": pkgs}]}}
            state = yaml.dump(state_contents)
        else:
            state_contents = {}
            for name, version in _pkgs.items():
                state_name = f"install_{name}"
                if include_version:
                    state_contents[state_name] = {
                        "pkg.installed": [{"name": name, "version": version}]
                    }
                else:
                    state_contents[state_name] = {"pkg.installed": [{"name": name}]}
            state = yaml.dump(state_contents)

        generate_sls(minion, state, "pkg")

    return True
