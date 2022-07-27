"""
Module for building state file

.. versionadded:: 3006

"""
import functools
import inspect
import logging
import os.path
import pathlib

import salt.daemons.masterapi  # pylint: disable=import-error
import salt.utils.files  # pylint: disable=import-error
import yaml


__virtualname__ = "describe"

__func_alias__ = {"all_": "all", "top_": "top"}


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def _exclude_from_all(func):
    """
    Decorator to exclude functions from all function
    """
    func.__all_excluded__ = True
    return func


def _get_all_single_describe_methods():
    """
    Get all methods that should be run in `all`
    """
    single_functions = [
        (name.replace("describe.", ""), loaded_func)
        for name, loaded_func in __salt__.items()
        if name.startswith("describe")
    ]
    names = {}
    for name, loaded_func in single_functions:
        if getattr(loaded_func, "__all_excluded__", False):
            continue
        names[name] = loaded_func
    return names


@_exclude_from_all
def all_(tgt, top=True, whitelist=None, blacklist=None, *args, **kwargs):
    """
    Run all describe methods against target

    CLI Example:

    .. code-block:: bash

        salt-run describe.all minion-tgt
    """
    if blacklist and whitelist:
        log.error("Only one of blacklist and whitelist can be provided")
        return False

    all_methods = _get_all_single_describe_methods()

    # Sanitize the whitelist and blacklist to the extremes if none are given
    if blacklist is None:
        blacklist = set()
    elif isinstance(blacklist, str):
        blacklist = {blacklist}
    elif isinstance(blacklist, (list, tuple)):
        blacklist = set(blacklist)

    if whitelist is None:
        whitelist = all_methods.keys()
    elif isinstance(whitelist, str):
        whitelist = {whitelist}
    elif isinstance(whitelist, (list, tuple)):
        whitelist = set(whitelist)

    allowed_method_names = whitelist - blacklist
    allowed_methods = {
        name: func
        for name, func in all_methods.items()
        if name in allowed_method_names
    }
    log.debug("Allowed methods in all: %s", allowed_methods)

    for name, func in allowed_methods.items():
        if name in blacklist or name not in whitelist:
            continue
        call_kwargs = kwargs.copy()
        get_args = inspect.getfullargspec(func).args
        for arg in args:
            if arg not in get_args:
                args.remove(arg)

        for kwarg in kwargs:
            if kwarg not in get_args:
                call_kwargs.pop(kwarg)

        log.debug(
            "Running describe.%s in all --  tgt: %s\targs: %s\tkwargs: %s",
            name,
            tgt,
            args,
            kwargs,
        )
        try:
            __salt__[f"describe.{name}"](tgt, *args, **call_kwargs)
        except TypeError as err:
            log.error(err.args[0])

    # generate the top file
    if top:
        __salt__["describe.top"](tgt)
    return True


@_exclude_from_all
def top_(tgt, tgt_type="glob", env="base"):
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


@_exclude_from_all
def pillar_top(tgt, tgt_type="glob", env="base"):
    """
    Add the generated pillars to top.sls

    CLI Example:

    .. code-block:: bash

        salt-run describe.top minion-tgt
    """
    # Gather minions based on tgt and tgt_type arguments
    masterapi = salt.daemons.masterapi.RemoteFuncs(__opts__)
    minions = masterapi.local.gather_minions(tgt, tgt_type)

    pillar_file_root = pathlib.Path(__salt__["config.get"]("pillar_roots:base")[0])
    top_file = pillar_file_root / "top.sls"

    if not top_file.is_file():
        top_file.touch()

    top_file_dict = {}

    with salt.utils.files.fopen(top_file, "r") as fp_:
        top_file_dict = yaml.safe_load(fp_.read())

    if env not in top_file_dict:
        top_file_dict[env] = {}

    for minion in minions:
        add_top = []
        for files in os.listdir(str(pillar_file_root / minion)):
            if files.endswith(".sls") and not files.startswith("init"):
                add_top.append(minion + "." + files.split(".sls")[0])

        if minion not in top_file_dict[env]:
            top_file_dict[env][minion] = add_top
        else:
            top_file_dict[env][minion].append(add_top)

    with salt.utils.files.fopen(top_file, "w") as fp_:
        fp_.write(yaml.dump(top_file_dict))

    return True
