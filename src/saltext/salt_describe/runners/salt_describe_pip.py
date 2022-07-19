"""
Module for building state file

.. versionadded:: 3006

"""
import logging

import yaml
from saltext.salt_describe.utils.salt_describe import generate_sls

__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def pip(tgt, tgt_type="glob", bin_env=None):
    """
    Gather installed pip libraries and build a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.pip minion-tgt

    """

    ret = __salt__["salt.execute"](
        tgt,
        "pip.freeze",
        tgt_type=tgt_type,
        bin_env=bin_env,
    )

    state_name = "installed_pip_libraries"
    state_fun = "pip.installed"

    for minion in list(ret.keys()):
        minion_pip_list = ret[minion]
        state_contents = {
            state_name: {
                state_fun: [{"pkgs": minion_pip_list}],
            },
        }

        state = yaml.dump(state_contents)

        generate_sls(minion, state, "pip")

    return True
