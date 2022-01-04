"""
Module for building state file

.. versionadded:: Sulfur

"""


import inspect
import logging
import os
import os.path
import pathlib
import sys
import yaml

import salt.utils.files
import salt.daemons.masterapi


__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def _generate_init(minion=None, env="base"):
    """
    Generate the init.sls for the minion or minions
    """
    state_file_root = __salt__["config.get"]("file_roots:base")[0]

    minion_state_root = "{}/{}".format(state_file_root, minion)
    if not os.path.exists(minion_state_root):
        os.mkdir(minion_state_root)

    minion_init_file = "{}/init.sls".format(minion_state_root)

    include_files = []
    for file in os.listdir(minion_state_root):
        if file.endswith(".sls") and file != "init.sls":
            _file = os.path.splitext(file)[0]
            include_files.append("moriarty.{}".format(_file))

    state_contents = {"include": include_files}

    with salt.utils.files.fopen(minion_init_file, "w") as fp_:
        fp_.write(yaml.dump(state_contents))

    return True


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

        _generate_init(minion)

    return True


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

        for path in file_contents[minion]:

            path_file = "{}/files/{}".format(minion_state_root, path)

            os.makedirs(os.path.dirname(path_file), exist_ok=True)

            with salt.utils.files.fopen(path_file, "w") as fp_:
                fp_.write(file_contents[minion][path])

        _generate_init(minion)

    return True


def all(tgt, top=True, exclude=None, *args, **kwargs):
    """
    Run all describe methods against target

    CLI Example:

    .. code-block:: bash

        salt-run describe.all minion-tgt
    """
    all_methods = ["pkg", "file"]
    for method in all_methods:
        if method == exclude:
            continue
        call_kwargs = kwargs.copy()
        get_args = inspect.getfullargspec(getattr(sys.modules[__name__],
                                                   method)).args
        for arg in args:
            if arg not in get_args:
                args.remove(arg)

        for kwarg in kwargs:
            if kwarg not in get_args:
                call_kwargs.pop(kwarg)

        try:
            ret = __salt__["describe.{}".format(method)](tgt, *args, **call_kwargs)
        except TypeError as err:
            log.error(err.args[0])

    # generate the top file
    if top:
        __salt__["describe.top"](tgt)
    return True


def top(tgt, tgt_type="glob", env="base"):
    """
    Add the generated states to top.sls

    CLI Example:

    .. code-block:: bash

        salt-run describe.top minion-tgt
    """
    # Gather minions based on tgt and tgt_type arguments
    masterapi = salt.daemons.masterapi.RemoteFuncs(__opts__)
    minions = masterapi.local.gather_minions(tgt, tgt_type)

    state_file_root = pathlib.Path(__salt__["config.get"]("file_roots:base")[0])
    top_file = state_file_root / "top.sls"

    if not top_file.is_file():
        top_file.touch()

    top_file_dict = {}

    with salt.utils.files.fopen(top_file, "r") as fp_:
        top_file_contents = yaml.safe_load(fp_.read())

    if env not in top_file_dict:
        top_file_dict[env] = {}

    for minion in minions:
        add_top = []
        for files in os.listdir(str(state_file_root / minion)):
            if files.endswith(".sls") and not files.startswith("init"):
                add_top.append(minion + "." + files.split(".sls")[0])

        if minion not in top_file_dict[env]:
            top_file_dict[env][minion] = add_top
        else:
            top_file_dict[env][minion].append(add_top)

    with salt.utils.files.fopen(top_file, "w") as fp_:
        fp_.write(yaml.dump(top_file_dict))

    return True
