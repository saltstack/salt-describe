# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.runners.salt_describe_pkgrepo as salt_describe_pkgrepo_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_pkgrepo_runner: {
            "__salt__": {"salt.execute": MagicMock()},
            "__opts__": {},
        },
    }


def test_pkgrepo_redhat():
    pkgrepo_list = {
        "minion": {
            "baseos": {
                "name": "CentOS Stream $releasever - BaseOS",
                "metalink": "https://mirrors.centos.org/metalink?repo=centos-baseos-$stream&arch=$basearch&protocol=https,http",
                "gpgkey": "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial",
                "gpgcheck": "1",
                "repo_gpgcheck": "0",
                "metadata_expire": "6h",
                "countme": "1",
                "enabled": "1",
                "file": "/etc/yum.repos.d/centos.repo",
            },
            "baseos-source": {
                "name": "CentOS Stream $releasever - BaseOS - Source",
                "metalink": "https://mirrors.centos.org/metalink?repo=centos-baseos-source-$stream&arch=source&protocol=https,http",
                "gpgkey": "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial",
                "gpgcheck": "1",
                "repo_gpgcheck": "0",
                "metadata_expire": "6h",
                "enabled": "0",
                "file": "/etc/yum.repos.d/centos.repo",
            },
            "appstream": {
                "name": "CentOS Stream $releasever - AppStream",
                "metalink": "https://mirrors.centos.org/metalink?repo=centos-appstream-$stream&arch=$basearch&protocol=https,http",
                "gpgkey": "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial",
                "gpgcheck": "1",
                "repo_gpgcheck": "0",
                "metadata_expire": "6h",
                "countme": "1",
                "enabled": "1",
                "file": "/etc/yum.repos.d/centos.repo",
            },
            "appstream-source": {
                "name": "CentOS Stream $releasever - AppStream - Source",
                "metalink": "https://mirrors.centos.org/metalink?repo=centos-appstream-source-$stream&arch=source&protocol=https,http",
                "gpgkey": "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial",
                "gpgcheck": "1",
                "repo_gpgcheck": "0",
                "metadata_expire": "6h",
                "enabled": "0",
                "file": "/etc/yum.repos.d/centos.repo",
            },
        }
    }

    mock_minion_data = ({}, {"os_family": "RedHat"}, {})

    redhat_sls_contents = {
        "appstream": {
            "pkgrepo.managed": [
                {"humanname": "CentOS Stream $releasever - AppStream"},
                {"gpgkey": "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial"},
                {"gpgcheck": "1"},
                {"enabled": "1"},
                {
                    "metalink": "https://mirrors.centos.org/metalink?repo=centos-appstream-$stream&arch=$basearch&protocol=https,http"
                },
            ]
        },
        "appstream-source": {
            "pkgrepo.managed": [
                {"humanname": "CentOS Stream $releasever - AppStream - Source"},
                {"gpgkey": "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial"},
                {"gpgcheck": "1"},
                {"enabled": "0"},
                {
                    "metalink": "https://mirrors.centos.org/metalink?repo=centos-appstream-source-$stream&arch=source&protocol=https,http"
                },
            ]
        },
        "baseos": {
            "pkgrepo.managed": [
                {"humanname": "CentOS Stream $releasever - BaseOS"},
                {"gpgkey": "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial"},
                {"gpgcheck": "1"},
                {"enabled": "1"},
                {
                    "metalink": "https://mirrors.centos.org/metalink?repo=centos-baseos-$stream&arch=$basearch&protocol=https,http"
                },
            ]
        },
        "baseos-source": {
            "pkgrepo.managed": [
                {"humanname": "CentOS Stream $releasever - BaseOS - Source"},
                {"gpgkey": "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial"},
                {"gpgcheck": "1"},
                {"enabled": "0"},
                {
                    "metalink": "https://mirrors.centos.org/metalink?repo=centos-baseos-source-$stream&arch=source&protocol=https,http"
                },
            ]
        },
    }
    redhat_sls = yaml.dump(redhat_sls_contents)

    with patch.dict(
        salt_describe_pkgrepo_runner.__salt__,
        {"salt.execute": MagicMock(return_value=pkgrepo_list)},
    ):
        with patch(
            "salt.utils.minions.get_minion_data", MagicMock(return_value=mock_minion_data)
        ) as minion_data_mock:
            with patch.object(salt_describe_pkgrepo_runner, "generate_files") as generate_mock:
                assert "Generated SLS file locations" in salt_describe_pkgrepo_runner.pkgrepo(
                    "minion"
                )
                minion_data_mock.assert_called_with("minion", {})
                generate_mock.assert_called_with(
                    {}, "minion", redhat_sls, sls_name="pkgrepo", config_system="salt"
                )


def test_pkgrepo_debian():
    pkgrepo_list = {
        "minion": {
            "http://us.archive.ubuntu.com/ubuntu": [
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["main", "restricted"],
                    "disabled": False,
                    "dist": "jammy",
                    "type": "deb",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "deb http://us.archive.ubuntu.com/ubuntu jammy main restricted",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["main", "restricted"],
                    "disabled": True,
                    "dist": "jammy",
                    "type": "deb-src",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "# deb-src http://us.archive.ubuntu.com/ubuntu jammy main restricted",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["main", "restricted"],
                    "disabled": False,
                    "dist": "jammy-updates",
                    "type": "deb",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "deb http://us.archive.ubuntu.com/ubuntu jammy-updates main restricted",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["main", "restricted"],
                    "disabled": True,
                    "dist": "jammy-updates",
                    "type": "deb-src",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "# deb-src http://us.archive.ubuntu.com/ubuntu jammy-updates main restricted",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["universe"],
                    "disabled": False,
                    "dist": "jammy",
                    "type": "deb",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "deb http://us.archive.ubuntu.com/ubuntu jammy universe",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["universe"],
                    "disabled": True,
                    "dist": "jammy",
                    "type": "deb-src",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "# deb-src http://us.archive.ubuntu.com/ubuntu jammy universe",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["universe"],
                    "disabled": False,
                    "dist": "jammy-updates",
                    "type": "deb",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "deb http://us.archive.ubuntu.com/ubuntu jammy-updates universe",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["universe"],
                    "disabled": True,
                    "dist": "jammy-updates",
                    "type": "deb-src",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "# deb-src http://us.archive.ubuntu.com/ubuntu jammy-updates universe",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["multiverse"],
                    "disabled": False,
                    "dist": "jammy",
                    "type": "deb",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "deb http://us.archive.ubuntu.com/ubuntu jammy multiverse",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["multiverse"],
                    "disabled": True,
                    "dist": "jammy",
                    "type": "deb-src",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "# deb-src http://us.archive.ubuntu.com/ubuntu jammy multiverse",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["multiverse"],
                    "disabled": False,
                    "dist": "jammy-updates",
                    "type": "deb",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "deb http://us.archive.ubuntu.com/ubuntu jammy-updates multiverse",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["multiverse"],
                    "disabled": True,
                    "dist": "jammy-updates",
                    "type": "deb-src",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "# deb-src http://us.archive.ubuntu.com/ubuntu jammy-updates multiverse",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["main", "restricted", "universe", "multiverse"],
                    "disabled": False,
                    "dist": "jammy-backports",
                    "type": "deb",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "deb http://us.archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["main", "restricted", "universe", "multiverse"],
                    "disabled": True,
                    "dist": "jammy-backports",
                    "type": "deb-src",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "# deb-src http://us.archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["main", "restricted"],
                    "disabled": False,
                    "dist": "jammy-security",
                    "type": "deb",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "deb http://us.archive.ubuntu.com/ubuntu jammy-security main restricted",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["main", "restricted"],
                    "disabled": True,
                    "dist": "jammy-security",
                    "type": "deb-src",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "# deb-src http://us.archive.ubuntu.com/ubuntu jammy-security main restricted",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["universe"],
                    "disabled": False,
                    "dist": "jammy-security",
                    "type": "deb",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "deb http://us.archive.ubuntu.com/ubuntu jammy-security universe",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["universe"],
                    "disabled": True,
                    "dist": "jammy-security",
                    "type": "deb-src",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "# deb-src http://us.archive.ubuntu.com/ubuntu jammy-security universe",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["multiverse"],
                    "disabled": False,
                    "dist": "jammy-security",
                    "type": "deb",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "deb http://us.archive.ubuntu.com/ubuntu jammy-security multiverse",
                    "architectures": [],
                },
                {
                    "file": "/etc/apt/sources.list",
                    "comps": ["multiverse"],
                    "disabled": True,
                    "dist": "jammy-security",
                    "type": "deb-src",
                    "uri": "http://us.archive.ubuntu.com/ubuntu",
                    "line": "# deb-src http://us.archive.ubuntu.com/ubuntu jammy-security multiverse",
                    "architectures": [],
                },
            ]
        }
    }

    mock_minion_data = ({}, {"os_family": "Debian"}, {})

    debian_sls_contents = {
        "deb http://us.archive.ubuntu.com/ubuntu jammy main restricted": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy"},
                {"refresh": False},
                {"disabled": False},
                {"comps": "main,restricted"},
            ]
        },
        "deb http://us.archive.ubuntu.com/ubuntu jammy multiverse": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy"},
                {"refresh": False},
                {"disabled": False},
                {"comps": "multiverse"},
            ]
        },
        "deb http://us.archive.ubuntu.com/ubuntu jammy universe": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy"},
                {"refresh": False},
                {"disabled": False},
                {"comps": "universe"},
            ]
        },
        "deb http://us.archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-backports"},
                {"refresh": False},
                {"disabled": False},
                {"comps": "main,restricted,universe,multiverse"},
            ]
        },
        "deb http://us.archive.ubuntu.com/ubuntu jammy-security main restricted": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-security"},
                {"refresh": False},
                {"disabled": False},
                {"comps": "main,restricted"},
            ]
        },
        "deb http://us.archive.ubuntu.com/ubuntu jammy-security multiverse": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-security"},
                {"refresh": False},
                {"disabled": False},
                {"comps": "multiverse"},
            ]
        },
        "deb http://us.archive.ubuntu.com/ubuntu jammy-security universe": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-security"},
                {"refresh": False},
                {"disabled": False},
                {"comps": "universe"},
            ]
        },
        "deb http://us.archive.ubuntu.com/ubuntu jammy-updates main restricted": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-updates"},
                {"refresh": False},
                {"disabled": False},
                {"comps": "main,restricted"},
            ]
        },
        "deb http://us.archive.ubuntu.com/ubuntu jammy-updates multiverse": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-updates"},
                {"refresh": False},
                {"disabled": False},
                {"comps": "multiverse"},
            ]
        },
        "deb http://us.archive.ubuntu.com/ubuntu jammy-updates universe": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-updates"},
                {"refresh": False},
                {"disabled": False},
                {"comps": "universe"},
            ]
        },
        "deb-src http://us.archive.ubuntu.com/ubuntu jammy main restricted": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy"},
                {"refresh": False},
                {"disabled": True},
                {"comps": "main,restricted"},
            ]
        },
        "deb-src http://us.archive.ubuntu.com/ubuntu jammy multiverse": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy"},
                {"refresh": False},
                {"disabled": True},
                {"comps": "multiverse"},
            ]
        },
        "deb-src http://us.archive.ubuntu.com/ubuntu jammy universe": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy"},
                {"refresh": False},
                {"disabled": True},
                {"comps": "universe"},
            ]
        },
        "deb-src http://us.archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-backports"},
                {"refresh": False},
                {"disabled": True},
                {"comps": "main,restricted,universe,multiverse"},
            ]
        },
        "deb-src http://us.archive.ubuntu.com/ubuntu jammy-security main restricted": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-security"},
                {"refresh": False},
                {"disabled": True},
                {"comps": "main,restricted"},
            ]
        },
        "deb-src http://us.archive.ubuntu.com/ubuntu jammy-security multiverse": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-security"},
                {"refresh": False},
                {"disabled": True},
                {"comps": "multiverse"},
            ]
        },
        "deb-src http://us.archive.ubuntu.com/ubuntu jammy-security universe": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-security"},
                {"refresh": False},
                {"disabled": True},
                {"comps": "universe"},
            ]
        },
        "deb-src http://us.archive.ubuntu.com/ubuntu jammy-updates main restricted": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-updates"},
                {"refresh": False},
                {"disabled": True},
                {"comps": "main,restricted"},
            ]
        },
        "deb-src http://us.archive.ubuntu.com/ubuntu jammy-updates multiverse": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-updates"},
                {"refresh": False},
                {"disabled": True},
                {"comps": "multiverse"},
            ]
        },
        "deb-src http://us.archive.ubuntu.com/ubuntu jammy-updates universe": {
            "pkgrepo.managed": [
                {"file": "/etc/apt/sources.list"},
                {"dist": "jammy-updates"},
                {"refresh": False},
                {"disabled": True},
                {"comps": "universe"},
            ]
        },
    }

    debian_sls = yaml.dump(debian_sls_contents)

    with patch.dict(
        salt_describe_pkgrepo_runner.__salt__,
        {"salt.execute": MagicMock(return_value=pkgrepo_list)},
    ):
        with patch(
            "salt.utils.minions.get_minion_data", MagicMock(return_value=mock_minion_data)
        ) as minion_data_mock:
            with patch.object(salt_describe_pkgrepo_runner, "generate_files") as generate_mock:
                assert "Generated SLS file locations" in salt_describe_pkgrepo_runner.pkgrepo(
                    "minion"
                )
                minion_data_mock.assert_called_with("minion", {})
                generate_mock.assert_called_with(
                    {}, "minion", debian_sls, sls_name="pkgrepo", config_system="salt"
                )
