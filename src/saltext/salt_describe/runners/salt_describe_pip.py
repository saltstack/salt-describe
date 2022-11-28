"""
Module for building state file

.. versionadded:: 3006

"""
import logging

import yaml
from saltext.salt_describe.utils.init import generate_files

__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def pip(tgt, tgt_type="glob", bin_env=None, config_system="salt"):
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

        generate_files(__opts__, minion, state, sls_name="pip", config_system=config_system)

    return True
