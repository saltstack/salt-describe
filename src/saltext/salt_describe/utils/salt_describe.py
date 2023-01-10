# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import pathlib

import salt.config
import salt.syspaths
import salt.utils.files
import yaml


def get_state_file_root(opts, env="base"):
    """
    Get the state file root
    """
    return pathlib.Path(opts.get("file_roots").get(env)[0])


def get_minion_state_file_root(opts, minion, env="base"):
    """
    Get the state file root for the given minion
    """
    return get_state_file_root(opts, env=env) / minion


def get_pillar_file_root(opts, env="base"):
    """
    Get the pillar root
    """
    return pathlib.Path(opts.get("pillar_roots").get(env)[0])


def get_minion_pillar_file_root(opts, minion, env="base"):
    """
    Get the pillar root for the given minion
    """
    return get_pillar_file_root(opts, env=env) / minion


def generate_files(opts, minion, state, sls_name="default", env="base"):
    """
    Generate an sls file for the minion with given state contents
    """
    minion_state_root = get_minion_state_file_root(opts, minion, env=env)
    minion_state_root.mkdir(parents=True, exist_ok=True)

    minion_state_file = minion_state_root / f"{sls_name}.sls"

    with salt.utils.files.fopen(minion_state_file, "w") as fp_:
        fp_.write(state)

    generate_init(opts, minion, env=env)
    return minion_state_file


def generate_init(opts, minion=None, env="base"):
    """
    Generate the init.sls for the minion or minions
    """
    minion_state_root = get_minion_state_file_root(opts, minion, env=env)
    minion_state_root.mkdir(parents=True, exist_ok=True)

    minion_init_file = minion_state_root / "init.sls"

    include_files = []
    for file in minion_state_root.iterdir():
        if file.suffix == ".sls" and file.stem != "init":
            _file = file.stem
            include_files.append(f"{minion}.{_file}")

    state_contents = {"include": include_files}

    with salt.utils.files.fopen(minion_init_file, "w") as fp_:
        fp_.write(yaml.dump(state_contents))

    return True


def generate_pillar_init(opts, minion=None, env="base"):
    """
    Generate the init.sls for the minion or minions
    """
    minion_pillar_root = get_minion_pillar_file_root(opts, minion, env=env)
    minion_pillar_root.mkdir(parents=True, exist_ok=True)

    minion_init_file = minion_pillar_root / "init.sls"

    include_files = []
    for file in minion_pillar_root.iterdir():
        if file.suffix == ".sls" and file.stem != "init":
            _file = file.stem
            include_files.append(f"{minion}.{_file}")

    pillar_contents = {"include": include_files}

    with salt.utils.files.fopen(minion_init_file, "w") as fp_:
        fp_.write(yaml.dump(pillar_contents))

    return True


def generate_pillars(opts, minion, pillar, sls_name="default", env="base"):
    """
    Generate pillar files for the minion to hold more sensitive information
    """
    minion_pillar_root = get_minion_pillar_file_root(opts, minion, env=env)
    minion_pillar_root.mkdir(parents=True, exist_ok=True)

    minion_pillar_file = minion_pillar_root / f"{sls_name}.sls"

    with salt.utils.files.fopen(minion_pillar_file, "w") as fp_:
        fp_.write(pillar)

    generate_pillar_init(opts, minion, env=env)
    return True
