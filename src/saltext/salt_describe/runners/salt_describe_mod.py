"""
Module for building state file

.. versionadded:: Sulfur

"""


import logging
import os
import yaml

import salt.utils.files

log = logging.getLogger(__name__)


def pkg(tgt, tgt_type="glob", include_version=True, single_state=True):
    """
    Gather installed pkgs on minions and build a state file.

    CLI Example:

    .. code-block:: bash

        salt '*' salt_describe.pkg

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
                state_name = "install_{}".format(name)
                if include_version:
                    state_contents[state_name] = {"pkg.installed": [{"name": name, "version": version}]}
                else:
                    state_contents[state_name] = {"pkg.installed": [{"name": name}]}
            state = yaml.dump(state_contents)

        state_file_root = __salt__["config.get"]("file_roots:base")[0]

        minion_state_root = "{}/{}".format(state_file_root, minion)
        if not os.path.exists(minion_state_root):
            os.mkdir(minion_state_root)

        minion_state_file = "{}/pkgs.sls".format(minion_state_root)

        with salt.utils.files.fopen(minion_state_file, "w") as fp_:
            fp_.write(state)

    return True


def file(tgt, paths, tgt_type="glob"):
    """
    Read a file on the minions and build a state file
    to managed a file.

    CLI Example:

    .. code-block:: bash

        salt '*' salt_describe.file /etc/salt/minion

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

            _file_mode = _file_stats[minion]['mode']
            _file_user = _file_stats[minion]['user']
            _file_group = _file_stats[minion]['group']

            if minion not in state_contents:
                state_contents[minion] = {}
            state_contents[minion][path] = {"file.managed": [{"source": "salt://{}/files/{}".format(minion, path),
                                                      "user": _file_user,
                                                      "group": _file_group,
                                                      "mode": _file_mode
            }]}

    for minion in list(state_contents.keys()):
        state = yaml.dump(state_contents[minion])

        state_file_root = __salt__["config.get"]("file_roots:base")[0]

        minion_state_root = "{}/{}".format(state_file_root, minion)
        if not os.path.exists(minion_state_root):
            os.mkdir(minion_state_root)

        minion_state_file = "{}/files.sls".format(minion_state_root)

        with salt.utils.files.fopen(minion_state_file, "w") as fp_:
            fp_.write(state)

    for minion in list(file_contents.keys()):
        for path in file_contents[minion]:

            path_file = "{}/files/{}".format(minion_state_root, path)

            os.makedirs(os.path.dirname(path_file), exist_ok=True)

            with salt.utils.files.fopen(path_file, "w") as fp_:
                fp_.write(file_contents[minion][path])

    return True


def top(tgt, tgt_type="glob", env="base"):
    """
    Add the generated states to top.sls

    CLI Example:

    .. code-block:: bash

        salt '*' salt_describe.top

    """

    state_file_root = __salt__["config.get"]("file_roots:base")[0]
    top_file = "{}/top.sls".format(state_file_root)

    with salt.utils.files.fopen(top_file, "r") as fp_:
        top_file_dict = yaml.load(fp_.read())

        #for 
        #if env in top_file_dict:
        #    if 

        breakpoint()

    return True
