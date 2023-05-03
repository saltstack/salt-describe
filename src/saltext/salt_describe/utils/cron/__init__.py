# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging

log = logging.getLogger(__name__)


def _parse_pre_cron(line, user, commented_cron_job=False):
    if line.startswith("#"):
        try:
            return _parse_pre_cron(line.lstrip("#").lstrip(), user, commented_cron_job=True)
        except Exception:  # pylint: disable-broad-except
            log.debug("Failed to parse commented line as cron in pre: %s", line)
            return "comment", None, line
    if line.startswith("@"):
        # Its a "special" line
        data = []
        comps = line.split()
        if len(comps) < 2:
            # Invalid line
            log.debug("Invalid special line, skipping: %s", line)
            return "unknown", line
        cmd = " ".join(comps[1:])
        data = [
            {"special": comps[0]},
            {"comment": None},
            {"commented": commented_cron_job},
            {"identifier": False},
            {"user": user},
        ]
        return "special", cmd, data
    elif line.find("=") > 0 and (" " not in line or line.index("=") < line.index(" ")):
        # Appears to be a ENV setup line
        if not commented_cron_job:
            comps = line.split("=", 1)
            name = comps[0]
            data = [{"value": comps[1]}, {"user": user}]
            return "env", name, data
    elif len(line.split(" ")) > 5:
        # Appears to be a standard cron line
        comps = line.split(" ")
        cmd = " ".join(comps[5:])
        data = [
            {"minute": comps[0]},
            {"hour": comps[1]},
            {"daymonth": comps[2]},
            {"month": comps[3]},
            {"dayweek": comps[4]},
            {"comment": None},
            {"identifier": False},
            {"commented": commented_cron_job},
            {"user": user},
        ]
        return "cron", cmd, data

    return "unknown", None, line
