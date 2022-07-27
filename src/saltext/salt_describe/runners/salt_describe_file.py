"""
Module for building state file

.. versionadded:: 3006

"""
import logging
import os

import salt.utils.files  # pylint: disable=import-error
import yaml
from saltext.salt_describe.utils.salt_describe import generate_init

__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def file(tgt, paths, tgt_type="glob"):
    """
    Read a file on the minions and build a state file
    to managed a file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.file minion-tgt /etc/salt/minion
    """

    if isinstance(paths, str):
        paths = [paths]

    state_contents = {}
    file_contents = {}
    for path in paths:
        _file_contents = __salt__["salt.execute"](
            tgt,
            "file.read",
            tgt_type=tgt_type,
            arg=[path],
        )

        _file_stats = __salt__["salt.execute"](
            tgt,
            "file.stats",
            tgt_type=tgt_type,
            arg=[path],
        )

        for minion in list(_file_contents.keys()):
            if minion not in file_contents:
                file_contents[minion] = {}
            file_contents[minion][path] = _file_contents[minion]

            _file_mode = _file_stats[minion]["mode"]
            _file_user = _file_stats[minion]["user"]
            _file_group = _file_stats[minion]["group"]

            if minion not in state_contents:
                state_contents[minion] = {}
            state_contents[minion][path] = {
                "file.managed": [
                    {
                        "source": f"salt://{minion}/files/{path}",
                        "user": _file_user,
                        "group": _file_group,
                        "mode": _file_mode,
                    }
                ]
            }

    for minion in list(state_contents.keys()):
        state = yaml.dump(state_contents[minion])

        state_file_root = __salt__["config.get"]("file_roots:base")[0]

        minion_state_root = f"{state_file_root}/{minion}"
        if not os.path.exists(minion_state_root):
            os.mkdir(minion_state_root)

        minion_state_file = f"{minion_state_root}/files.sls"

        with salt.utils.files.fopen(minion_state_file, "w") as fp_:
            fp_.write(state)

        for path in file_contents[minion]:

            path_file = f"{minion_state_root}/files/{path}"

            os.makedirs(os.path.dirname(path_file), exist_ok=True)

            with salt.utils.files.fopen(path_file, "w") as fp_:
                fp_.write(file_contents[minion][path])

        generate_init(__opts__, minion)

    return True
