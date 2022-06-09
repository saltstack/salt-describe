"""
Module for building state file

.. versionadded:: 3006

"""
import functools
import inspect
import logging
import os.path
import pathlib
import sys

import salt.daemons.masterapi
import salt.utils.files
import yaml


__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def _exclude_from_all(func):
    functools.wraps(func)
    func.__all_excluded__ = True
    return func


def _generate_pillar_init(minion=None, env="base"):
    """
    Generate the init.sls for the minion or minions
    """
    pillar_file_root = pathlib.Path(__salt__["config.get"]("pillar_roots:base")[0])

    minion_pillar_root = pillar_file_root / minion
    if not os.path.exists(minion_pillar_root):
        os.mkdir(minion_pillar_root)

    minion_init_file = f"{minion_pillar_root}/init.sls"

    include_files = []
    for file in os.listdir(minion_pillar_root):
        if file.endswith(".sls") and file != "init.sls":
            _file = os.path.splitext(file)[0]
            include_files.append(f"{minion}.{_file}")

    pillar_contents = {"include": include_files}

    with salt.utils.files.fopen(minion_init_file, "w") as fp_:
        fp_.write(yaml.dump(pillar_contents))

    return True


def _generate_init(minion=None, env="base"):
    """
    Generate the init.sls for the minion or minions
    """
    state_file_root = __salt__["config.get"]("file_roots:base")[0]

    minion_state_root = f"{state_file_root}/{minion}"
    if not os.path.exists(minion_state_root):
        os.mkdir(minion_state_root)

    minion_init_file = f"{minion_state_root}/init.sls"

    include_files = []
    for file in os.listdir(minion_state_root):
        if file.endswith(".sls") and file != "init.sls":
            _file = os.path.splitext(file)[0]
            include_files.append(f"{minion}.{_file}")

    state_contents = {"include": include_files}

    with salt.utils.files.fopen(minion_init_file, "w") as fp_:
        fp_.write(yaml.dump(state_contents))

    return True


def _generate_sls(minion, state, sls_name="default"):
    state_file_root = pathlib.Path(__salt__["config.get"]("file_roots:base")[0])

    minion_state_root = state_file_root / minion
    if not os.path.exists(minion_state_root):
        os.mkdir(minion_state_root)

    minion_state_file = minion_state_root / f"{sls_name}.sls"

    with salt.utils.files.fopen(minion_state_file, "w") as fp_:
        fp_.write(state)

    _generate_init(minion)
    return True


def _generate_pillars(minion, pillar, sls_name="default"):
    pillar_file_root = pathlib.Path(__salt__["config.get"]("pillar_roots:base")[0])

    minion_pillar_root = pillar_file_root / minion
    if not os.path.exists(minion_pillar_root):
        os.mkdir(minion_pillar_root)

    minion_pillar_file = minion_pillar_root / f"{sls_name}.sls"

    with salt.utils.files.fopen(minion_pillar_file, "w") as fp_:
        fp_.write(pillar)

    _generate_pillar_init(minion)
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
                state_name = f"install_{name}"
                if include_version:
                    state_contents[state_name] = {
                        "pkg.installed": [{"name": name, "version": version}]
                    }
                else:
                    state_contents[state_name] = {"pkg.installed": [{"name": name}]}
            state = yaml.dump(state_contents)

        _generate_sls(minion, state, "pkg")

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

        _generate_init(minion)

    return True


def user(tgt, require_groups=False, tgt_type="glob"):
    """
    read users on the minions and build a state file
    to manage the users.

    CLI Example:

    .. code-block:: bash

        salt-run describe.user minion-tgt
    """

    state_contents = {}
    if require_groups is True:
        __salt__["describe.group"](tgt=tgt, include_members=False, tgt_type=tgt_type)

    users = __salt__["salt.execute"](
        tgt,
        "user.getent",
        tgt_type=tgt_type,
    )

    pillars = {"users": {}}
    for minion in list(users.keys()):
        for user in users[minion]:
            shadow = __salt__["salt.execute"](
                minion, "shadow.info", arg=[user["name"]], tgt_type="glob"
            )[minion]

            homeexists = __salt__["salt.execute"](
                minion, "file.directory_exists", arg=[user["home"]], tgt_type="glob"
            )[minion]
            username = user["name"]
            payload = [
                {"name": username},
                {"uid": user["uid"]},
                {"gid": user["gid"]},
                {"allow_uid_change": True},
                {"allow_gid_change": True},
                {"home": user["home"]},
                {"shell": user["shell"]},
                {"groups": user["groups"]},
                {"password": f'{{{{ salt["pillar.get"]("users:{username}","*") }}}}'},
                {"date": shadow["lstchg"]},
                {"mindays": shadow["min"]},
                {"maxdays": shadow["max"]},
                {"inactdays": shadow["inact"]},
                {"expire": shadow["expire"]},
            ]
            if homeexists:
                payload.append({"createhome": True})
            else:
                payload.append({"createhome": False})
            # GECOS
            if user["fullname"]:
                payload.append({"fullname": user["fullname"]})
            if user["homephone"]:
                payload.append({"homephone": user["homephone"]})
            if user["other"]:
                payload.append({"other": user["other"]})
            if user["roomnumber"]:
                payload.append({"roomnumber": user["roomnumber"]})
            if user["workphone"]:
                payload.append({"workphone": user["workphone"]})

            state_contents[f"user-{username}"] = {"user.present": payload}
            passwd = shadow["passwd"]
            if passwd != "*":
                pillars["users"].update({user["name"]: f"{passwd}"})

        state = yaml.dump(state_contents)
        pillars = yaml.dump(pillars)
        _generate_sls(minion, state, "users")
        _generate_pillars(minion, pillars, "users")
    return True


def group(tgt, include_members=False, tgt_type="glob"):
    """
    read groups on the minions and build a state file
    to managed th groups.

    CLI Example:

    .. code-block:: bash

        salt-run describe.group minion-tgt
    """
    groups = __salt__["salt.execute"](
        tgt,
        "group.getent",
        tgt_type=tgt_type,
    )

    state_contents = {}
    for minion in list(groups.keys()):
        for group in groups[minion]:
            groupname = group["name"]
            payload = [{"name": groupname}, {"gid": group["gid"]}]
            if include_members is True:
                payload.append({"members": group["members"]})
            state_contents[f"group-{groupname}"] = {"group.present": payload}

        state = yaml.dump(state_contents)

        _generate_sls(minion, state, "groups")

    return True


def service(tgt, tgt_type="glob"):
    """
    Gather enabled and disabled services on minions and build a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.service minion-tgt

    """

    enabled_services = __salt__["salt.execute"](
        tgt,
        "service.get_enabled",
        tgt_type=tgt_type,
    )

    disabled_services = __salt__["salt.execute"](
        tgt,
        "service.get_disabled",
        tgt_type=tgt_type,
    )

    service_status = __salt__["salt.execute"](
        tgt,
        "service.status",
        "*",
        tgt_type=tgt_type,
    )

    for minion in list(service_status.keys()):
        _services = service_status[minion]

        state_contents = {}
        for service, status in _services.items():
            state_name = f"{service}"
            _enabled = service in enabled_services.get(minion)
            _disabled = service in disabled_services.get(minion)

            if status:
                service_function = "service.running"
            else:
                service_function = "service.dead"

            if _enabled:
                state_contents[state_name] = {service_function: [{"enable": True}]}
            elif _disabled:
                state_contents[state_name] = {service_function: [{"enable": False}]}
            else:
                state_contents[state_name] = {service_function: []}

        state = yaml.dump(state_contents)
        _generate_sls(minion, state, "services")

    return True


def host(tgt, tgt_type="glob"):
    """
    Gather /etc/hosts file content on minions and build a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.host minion-tgt

    """
    ret = __salt__["salt.execute"](
        tgt,
        "hosts.list_hosts",
        tgt_type=tgt_type,
    )

    for minion in list(ret.keys()):
        content = ret[minion]
        count = 0
        state_contents = {}
        comment = []
        for key, value in content.items():
            sls_id = f"host_file_content_{count}"
            state_func = "host.present"
            if key.startswith("comment"):
                pass
            else:
                state_contents[sls_id] = {state_func: [{"ip": []}, {"names": []}]}
                state_contents[sls_id][state_func][0]["ip"] = key
                state_contents[sls_id][state_func][1]["names"] = value["aliases"]
                count += 1

        state = yaml.dump(state_contents)
        _generate_sls(minion, state, "host")

    return True


def timezone(tgt, tgt_type="glob"):
    """
    Gather the timezone data for minions and generate a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.timezone minion-tgt

    """

    timezones = __salt__["salt.execute"](
        tgt,
        "timezone.get_zone",
        tgt_type=tgt_type,
    )

    for minion in list(timezones.keys()):
        timezone = timezones[minion]

        state_contents = {}
        state_name = f"{timezone}"
        state_contents = {timezone: {"timezone.system": []}}

        state = yaml.dump(state_contents)

        _generate_sls(minion, state, "timezone")

    return True


def _get_all_single_describe_methods():
    """
    Get all methods that should be run in `all`
    """
    single_functions = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
    names = {}
    for name, func in single_functions:
        if name.startswith("_"):
            continue
        if getattr(func, "__all_excluded__", False):
            continue
        names[name] = func
    return names


def sysctl(tgt, sysctl, tgt_type="glob"):
    """
    read sysctl on the minions and build a state file
    to managed the sysctl settings.

    CLI Example:

    .. code-block:: bash

        salt-run describe.sysctl minion-tgt '[vm.swappiness,vm.dirty_ratio]'
    """
    sysctls = __salt__["salt.execute"](
        tgt,
        "sysctl.show",
        tgt_type=tgt_type,
    )

    state_contents = {}
    for minion in list(sysctls.keys()):
        for current in sysctl:
            if current in sysctls[minion].keys():
                payload = [{"name": current}, {"value": sysctls[minion][current]}]
                state_contents[f"sysctl-{current}"] = {"sysctl.present": payload}
            else:
                log.error(f"{current} not found in sysctl")

        state = yaml.dump(state_contents)
        _generate_sls(minion, state, "sysctl")

    return True


def iptables(tgt, tgt_type="glob"):
    """
    Gather the iptable rules for minions and generate a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.iptables minion-tgt
    """
    rules = __salt__["salt.execute"](
        tgt,
        "iptables.get_rules",
        tgt_type=tgt_type,
    )
    for minion in list(rules.keys()):
        state_contents = {}
        state_func = "iptables.append"

        rule = rules[minion]
        table = list(rule)[0]
        chains = list(rule[table])
        count = 0
        for chain in chains:

            _rules = rule[table][chain]["rules"]
            if not _rules:
                break
            for _rule in _rules:
                kwargs = [{"chain": chain}, {"table": table}]
                state_id = f"add_iptables_rule_{count}"
                state_contents[state_id] = {state_func: []}
                for kwarg in list(_rule.keys()):
                    kwargs.append({kwarg.replace("_", "-"): " ".join(_rule[kwarg])})
                state_contents[state_id][state_func] = kwargs
                count += 1

        state = yaml.dump(state_contents)

        _generate_sls(minion, state, "iptables")

    return True


def firewalld(tgt, tgt_type="glob"):
    """
    Gather the firewalld rules for minions and generate a state file.

    CLI Example:

    .. code-block:: bash

        salt-run describe.firewalld minion-tgt
    """
    rules = __salt__["salt.execute"](
        tgt,
        "firewalld.list_all",
        tgt_type=tgt_type,
    )
    for minion in list(rules.keys()):
        state_contents = {}
        state_func = "firewalld.present"

        rule = rules[minion]
        zones = rule.keys()
        count = 0
        for zone in zones:
            state_id = f"add_firewalld_rule_{count}"
            state_contents[state_id] = {state_func: []}
            kwargs = [
                x
                for x in (
                    {"name": zone},
                    {"block_icmp": rule[zone]["icmp-blocks"]},
                    {"ports": rule[zone]["ports"]},
                    {"port_fwd": rule[zone]["forward-ports"]},
                    {"services": rule[zone]["services"][0].split()},
                    {"interfaces": rule[zone]["interfaces"]},
                    {"sources": rule[zone]["sources"]},
                    {"rich_rules": rule[zone]["rich rules"]},
                )
                if not list(x.values()) == [[""]] or not list(x.values())
            ]
            if rule[zone]["target"] == "default":
                kwargs["default"] = True
            if rule[zone]["masquerade"] == "yes":
                kwargs["masquerade"] = True

            state_contents[state_id][state_func] = kwargs
            count += 1

        state = yaml.dump(state_contents)

        _generate_sls(minion, state, "firewalld")

    return True


@_exclude_from_all
def all(tgt, top=True, exclude=None, *args, **kwargs):
    """
    Run all describe methods against target

    CLI Example:

    .. code-block:: bash

        salt-run describe.all minion-tgt
    """
    all_methods = _get_all_single_describe_methods()
    if exclude is None:
        exclude = []
    elif isinstance(exclude, str):
        exclude = [exclude]
    for name, func in all_methods.items():
        if name in exclude:
            continue
        call_kwargs = kwargs.copy()
        get_args = inspect.getfullargspec(func).args
        for arg in args:
            if arg not in get_args:
                args.remove(arg)

        for kwarg in kwargs:
            if kwarg not in get_args:
                call_kwargs.pop(kwarg)

        try:
            ret = __salt__[f"describe.{name}"](tgt, *args, **call_kwargs)
        except TypeError as err:
            log.error(err.args[0])

    # generate the top file
    if top:
        __salt__["describe.top"](tgt)
    return True


@_exclude_from_all
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
