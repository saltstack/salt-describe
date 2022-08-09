"""
Module for building state file

.. versionadded:: 3006

"""
import logging
import os
import pathlib

import salt.utils.files  # pylint: disable=import-error
import yaml
from saltext.salt_describe.utils.salt_describe import generate_sls, get_minion_state_file_root

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
        minion_state_root = get_minion_state_file_root(__opts__, minion)

        for path in file_contents[minion]:
            path_obj = pathlib.Path(path)
            path_file = minion_state_root / "files" / path_obj.relative_to(path_obj.anchor)
            path_file.parent.mkdir(parents=True, exist_ok=True)

            with salt.utils.files.fopen(path_file, "w") as fp_:
                fp_.write(file_contents[minion][path])

        generate_sls(__opts__, minion, state, sls_name="files")

    return True
