# pylint: disable=line-too-long
import logging
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
import salt.config  # pylint: disable=import-error
import salt.runners.salt as salt_runner  # pylint: disable=import-error
import saltext.salt_describe.runners.salt_describe as salt_describe_runner
import saltext.salt_describe.runners.salt_describe_pkgrepo as salt_describe_pkgrepo_runner

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"salt.execute": salt_runner.execute},
        "__opts__": salt.config.DEFAULT_MASTER_OPTS.copy(),
    }
    return {
        salt_describe_runner: module_globals,
        salt_describe_pkgrepo_runner: module_globals,
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

    expected_calls = [
        call().write("include:\n- minion.pkgrepo\n"),
        call().write(
            "appstream:\n  pkgrepo.managed:\n  - humanname: CentOS Stream $releasever - AppStream\n  - gpgkey: file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial\n  - gpgcheck: '1'\n  - enabled: '1'\n  - metalink: https://mirrors.centos.org/metalink?repo=centos-appstream-$stream&arch=$basearch&protocol=https,http\nappstream-source:\n  pkgrepo.managed:\n  - humanname: CentOS Stream $releasever - AppStream - Source\n  - gpgkey: file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial\n  - gpgcheck: '1'\n  - enabled: '0'\n  - metalink: https://mirrors.centos.org/metalink?repo=centos-appstream-source-$stream&arch=source&protocol=https,http\nbaseos:\n  pkgrepo.managed:\n  - humanname: CentOS Stream $releasever - BaseOS\n  - gpgkey: file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial\n  - gpgcheck: '1'\n  - enabled: '1'\n  - metalink: https://mirrors.centos.org/metalink?repo=centos-baseos-$stream&arch=$basearch&protocol=https,http\nbaseos-source:\n  pkgrepo.managed:\n  - humanname: CentOS Stream $releasever - BaseOS - Source\n  - gpgkey: file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial\n  - gpgcheck: '1'\n  - enabled: '0'\n  - metalink: https://mirrors.centos.org/metalink?repo=centos-baseos-source-$stream&arch=source&protocol=https,http\n"
        ),
    ]
    mock_minion_data = ({}, {"os_family": "RedHat"}, {})

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=pkgrepo_list)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=["/srv/salt", "/srv/spm/salt"])},
        ):
            with patch("os.listdir", return_value=["pkgrepo.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    with patch(
                        "salt.utils.minions.get_minion_data",
                        MagicMock(return_value=mock_minion_data),
                    ):
                        assert salt_describe_pkgrepo_runner.pkgrepo("minion") is True
                        open_mock.assert_has_calls(expected_calls, any_order=True)


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

    expected_calls = [
        call().write("include:\n- minion.pkgrepo\n"),
        call().write(
            "deb http://us.archive.ubuntu.com/ubuntu jammy main restricted:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy\n  - refresh: false\n  - disabled: false\n  - comps: main,restricted\ndeb http://us.archive.ubuntu.com/ubuntu jammy multiverse:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy\n  - refresh: false\n  - disabled: false\n  - comps: multiverse\ndeb http://us.archive.ubuntu.com/ubuntu jammy universe:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy\n  - refresh: false\n  - disabled: false\n  - comps: universe\ndeb http://us.archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-backports\n  - refresh: false\n  - disabled: false\n  - comps: main,restricted,universe,multiverse\ndeb http://us.archive.ubuntu.com/ubuntu jammy-security main restricted:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-security\n  - refresh: false\n  - disabled: false\n  - comps: main,restricted\ndeb http://us.archive.ubuntu.com/ubuntu jammy-security multiverse:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-security\n  - refresh: false\n  - disabled: false\n  - comps: multiverse\ndeb http://us.archive.ubuntu.com/ubuntu jammy-security universe:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-security\n  - refresh: false\n  - disabled: false\n  - comps: universe\ndeb http://us.archive.ubuntu.com/ubuntu jammy-updates main restricted:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-updates\n  - refresh: false\n  - disabled: false\n  - comps: main,restricted\ndeb http://us.archive.ubuntu.com/ubuntu jammy-updates multiverse:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-updates\n  - refresh: false\n  - disabled: false\n  - comps: multiverse\ndeb http://us.archive.ubuntu.com/ubuntu jammy-updates universe:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-updates\n  - refresh: false\n  - disabled: false\n  - comps: universe\ndeb-src http://us.archive.ubuntu.com/ubuntu jammy main restricted:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy\n  - refresh: false\n  - disabled: true\n  - comps: main,restricted\ndeb-src http://us.archive.ubuntu.com/ubuntu jammy multiverse:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy\n  - refresh: false\n  - disabled: true\n  - comps: multiverse\ndeb-src http://us.archive.ubuntu.com/ubuntu jammy universe:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy\n  - refresh: false\n  - disabled: true\n  - comps: universe\ndeb-src http://us.archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-backports\n  - refresh: false\n  - disabled: true\n  - comps: main,restricted,universe,multiverse\ndeb-src http://us.archive.ubuntu.com/ubuntu jammy-security main restricted:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-security\n  - refresh: false\n  - disabled: true\n  - comps: main,restricted\ndeb-src http://us.archive.ubuntu.com/ubuntu jammy-security multiverse:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-security\n  - refresh: false\n  - disabled: true\n  - comps: multiverse\ndeb-src http://us.archive.ubuntu.com/ubuntu jammy-security universe:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-security\n  - refresh: false\n  - disabled: true\n  - comps: universe\ndeb-src http://us.archive.ubuntu.com/ubuntu jammy-updates main restricted:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-updates\n  - refresh: false\n  - disabled: true\n  - comps: main,restricted\ndeb-src http://us.archive.ubuntu.com/ubuntu jammy-updates multiverse:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-updates\n  - refresh: false\n  - disabled: true\n  - comps: multiverse\ndeb-src http://us.archive.ubuntu.com/ubuntu jammy-updates universe:\n  pkgrepo.managed:\n  - file: /etc/apt/sources.list\n  - dist: jammy-updates\n  - refresh: false\n  - disabled: true\n  - comps: universe\n"
        ),
    ]
    mock_minion_data = ({}, {"os_family": "Debian"}, {})

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=pkgrepo_list)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=["/srv/salt", "/srv/spm/salt"])},
        ):
            with patch("os.listdir", return_value=["pkgrepo.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    with patch(
                        "salt.utils.minions.get_minion_data",
                        MagicMock(return_value=mock_minion_data),
                    ):
                        assert salt_describe_pkgrepo_runner.pkgrepo("minion") is True
                        open_mock.assert_has_calls(expected_calls, any_order=True)


# pylint: enable=line-too-long
