"""
Module for building state file

.. versionadded:: 3006

"""
import inspect
import logging
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
def all_(tgt, top=True, include=None, exclude=None, **kwargs):
    """
    Run all describe methods against target.

    One of either a exclude or include can be given to specify
    which functions to run.  These can be either a string or python list.

    CLI Example:

    .. code-block:: bash

        salt-run describe.all minion-tgt exclude='["file", "user"]'

    You can supply args and kwargs to functions that require them as well.
    These are passed as explicit kwargs.

    CLI Example:

    .. code-block:: bash

        salt-run describe.all minion-tgt include='["file", "pip"]' paths='["/tmp/testfile", "/tmp/testfile2"]'

    If two functions take an arg or kwarg of the same name, you can differentiate them
    by prefixing the argument name.

    CLI Example:

    .. code-block:: bash

        salt-run describe.all minion-tgt include='["file", "pip"]' file_paths='["/tmp/testfile", "/tmp/testfile2"]'
    """
    if exclude and include:
        log.error("Only one of exclude and include can be provided")
        return False

    all_methods = _get_all_single_describe_methods()

    # Sanitize the include and exclude to the extremes if none are given
    if exclude is None:
        exclude = set()
    elif isinstance(exclude, str):
        exclude = {exclude}
    elif isinstance(exclude, (list, tuple)):
        exclude = set(exclude)

    if include is None:
        include = all_methods.keys()
    elif isinstance(include, str):
        include = {include}
    elif isinstance(include, (list, tuple)):
        include = set(include)

    # The set difference gives us all the allowed methods here
    allowed_method_names = include - exclude
    allowed_methods = {
        name: func for name, func in all_methods.items() if name in allowed_method_names
    }
    log.debug("Allowed methods in all: %s", allowed_methods)

    for name, func in allowed_methods.items():
        if name in exclude or name not in include:
            continue

        args, varargs, varkw, defaults, *_ = inspect.getfullargspec(func)
        kwargs_sig = {}
        if defaults:
            num_defaults = len(defaults)
            for idx in range(num_defaults):
                kwargs_sig[args[-num_defaults + idx]] = defaults[idx]
            args_sig = args[:-num_defaults]

        # Let's deal with positional args first, short circuit if invalid
        # The first argument will always be the minion target
        call_args = [tgt]
        for arg in args_sig[1:]:
            named_arg = f"{name}_{arg}"
            if arg in kwargs:
                call_args.append(kwargs[arg])
            elif named_arg in kwargs:
                # We don't need that kwarg anymore, pop it
                call_args.append(kwargs.pop(named_arg))
            else:
                log.error("Missing positional arg %s for describe.%s", arg, name)
                return False

        # Add the arbitrary positional arguments
        named_varargs = f"{name}_{varargs}"
        if named_varargs in kwargs:
            call_args.extend(kwargs.pop(named_varargs, []))
        else:
            call_args.extend(kwargs.get(varargs, []))

        # Let's form the call_kwargs now
        call_kwargs = {}
        for kwarg in kwargs_sig:
            named_kwarg = f"{name}_{kwarg}"
            if kwarg in kwargs:
                call_kwargs[kwarg] = kwargs[kwarg]
            elif named_kwarg in kwargs:
                # We don't need that kwarg anymore, pop it
                call_kwargs[kwarg] = kwargs.pop(named_kwarg)

        # Add the arbitrary keyword arguments
        named_varkw = f"{name}_{varkw}"
        if named_varkw in kwargs:
            call_kwargs.update(kwargs.pop(named_varkw, {}))
        else:
            call_kwargs.update(kwargs.get(varkw, {}))

        log.debug(
            "Running describe.%s in all --  tgt: %s\targs: %s\tkwargs: %s",
            name,
            tgt,
            call_args,
            call_kwargs,
        )

        try:
            # This follows the unwritten standard that the minion target must be the first argument
            __salt__[f"describe.{name}"](*call_args, **call_kwargs)
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
        top_file_dict = yaml.safe_load(fp_.read())

    if env not in top_file_dict:
        top_file_dict[env] = {}

    for minion in minions:
        add_top = []
        minion_file_root = state_file_root / minion
        for file in minion_file_root.iterdir():
            if file.suffix == ".sls" and file.stem != "init":
                add_top.append(minion + "." + file.stem)

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
        minion_pillar_root = pillar_file_root / minion
        for file in minion_pillar_root.iterdir():
            if file.suffix == ".sls" and file.stem != "init":
                add_top.append(minion + "." + file.stem)

        if minion not in top_file_dict[env]:
            top_file_dict[env][minion] = add_top
        else:
            top_file_dict[env][minion].append(add_top)

    with salt.utils.files.fopen(top_file, "w") as fp_:
        fp_.write(yaml.dump(top_file_dict))

    return True
