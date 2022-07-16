import logging
import pathlib
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
import salt.config
import salt.runners.salt as salt_runner
import saltext.salt_describe.runners.salt_describe as salt_describe_runner
import saltext.salt_describe.runners.salt_describe_pkg as salt_describe_pkg_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"salt.execute": salt_runner.execute},
        "__opts__": salt.config.DEFAULT_MASTER_OPTS.copy(),
    }
    return {
        salt_describe_runner: module_globals,
        salt_describe_pkg_runner: module_globals,
    }


def test_pkg():
    pkg_list = {
        "minion": {
            "pkg1": "0.1.2-3",
            "pkg2": "1.2rc5-3",
            "pkg3": "2.3.4-5",
            "pk4": "3.4-5",
            "pkg5": "4.5.6-7",
        }
    }

    expected_calls = [
        call().write(
            "installed_packages:\n  pkg.installed:\n  - pkgs:\n    - pkg1: 0.1.2-3\n    - pkg2: 1.2rc5-3\n    - pkg3: 2.3.4-5\n    - pk4: 3.4-5\n    - pkg5: 4.5.6-7\n"
        ),
        call().write("include:\n- minion.pkgs\n"),
    ]
    with patch.dict(
        salt_describe_pkg_runner.__salt__, {"salt.execute": MagicMock(return_value=pkg_list)}
    ):
        with patch.dict(
            salt_describe_pkg_runner.__salt__,
            {"config.get": MagicMock(return_value=["/srv/salt", "/srv/spm/salt"])},
        ):
            with patch("os.listdir", return_value=["pkgs.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_pkg_runner.pkg("minion") == True
                    open_mock.assert_has_calls(expected_calls, any_order=True)


def test_group():
    group_getent = {
        "minion": [
            {"gid": 4, "members": ["syslog", "whytewolf"], "name": "adm", "passwd": "x"},
            {"gid": 0, "members": [], "name": "root", "passwd": "x"},
        ]
    }

    expected_calls = [
        call().write(
            "group-adm:\n  group.present:\n  - name: adm\n  - gid: 4\ngroup-root:\n  group.present:\n  - name: root\n  - gid: 0\n"
        ),
        call().write("include:\n- minion.groups\n"),
    ]

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=group_getent)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=["/srv/salt", "/srv/spm/salt"])},
        ):
            with patch("os.listdir", return_value=["groups.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_runner.group("minion") == True
                    open_mock.return_value.write.assert_has_calls(expected_calls, any_order=True)


def test_host(tmp_path):
    """
    test describe.host
    """
    host_list = {
        "poc-minion": {
            "comment-0": ["# Host addresses"],
            "comment-1": ["# comment"],
            "127.0.0.1": {"aliases": ["localhost"]},
            "127.0.1.1": {"aliases": ["megan-precision5550"]},
            "::1": {"aliases": ["localhost", "ip6-localhost", "ip6-loopback"]},
            "ff02::1": {"aliases": ["ip6-allnodes"]},
            "ff02::2": {"aliases": ["ip6-allrouters"]},
        }
    }

    expected_content = {
        "host_file_content_0": {"host.present": [{"ip": "127.0.0.1"}, {"names": ["localhost"]}]},
        "host_file_content_1": {
            "host.present": [{"ip": "127.0.1.1"}, {"names": ["megan-precision5550"]}]
        },
        "host_file_content_2": {
            "host.present": [
                {"ip": "::1"},
                {"names": ["localhost", "ip6-localhost", "ip6-loopback"]},
            ]
        },
        "host_file_content_3": {"host.present": [{"ip": "ff02::1"}, {"names": ["ip6-allnodes"]}]},
        "host_file_content_4": {"host.present": [{"ip": "ff02::2"}, {"names": ["ip6-allrouters"]}]},
    }

    host_file = tmp_path / "poc-minion" / "host.sls"
    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=host_list)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[tmp_path])},
        ):
            assert salt_describe_runner.host("minion") == True
            with open(host_file) as fp:
                content = yaml.safe_load(fp.read())
                assert content == expected_content


def test_timezone(tmp_path):
    """
    test describe.host
    """
    timezone_list = {"poc-minion": "America/Los_Angeles"}

    expected_content = {"America/Los_Angeles": {"timezone.system": []}}

    host_file = tmp_path / "poc-minion" / "timezone.sls"
    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=timezone_list)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[tmp_path])},
        ):
            assert salt_describe_runner.host("minion") == True
            with open(host_file) as fp:
                content = yaml.safe_load(fp.read())
                assert content == expected_content


def test_pip(tmp_path):
    pip_list = {
        "minion": [
            "requests==0.1.2",
            "salt==3004.1",
            "argcomplete==2.3.4-5",
        ],
    }

    expected_sls_write = yaml.dump(
        {
            "installed_pip_libraries": {"pip.installed": [{"pkgs": pip_list["minion"]}]},
        }
    )
    expected_include_write = yaml.dump({"include": ["minion.pip"]})
    expected_calls = [
        call().write(expected_sls_write),
        call().write(expected_include_write),
    ]
    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=pip_list)}
    ):
        tmp_state_root = pathlib.Path(tmp_path, "srv", "salt")
        tmp_state_root.mkdir(parents=True, exist_ok=True)
        unused_dir = pathlib.Path(tmp_path, "srv", "spm", "salt")
        unused_dir.mkdir(parents=True, exist_ok=True)
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[str(tmp_state_root), str(unused_dir)])},
        ):
            with patch("os.listdir", return_value=["pip.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_runner.pip("minion") == True
                    open_mock.assert_has_calls(expected_calls, any_order=True)


def test_sysctl():
    sysctl_show = {"minion": {"vm.swappiness": 60, "vm.vfs_cache_pressure": 100}}

    expected_calls = [
        call().write(
            "sysctl-vm.swappiness:\n  sysctl.present:\n  - name: vm.swappiness\n  - value: 60\n"
        ),
        call().write("include:\n- minion.sysctl\n"),
    ]

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=sysctl_show)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=["/srv/salt", "/srv/spm/salt"])},
        ):
            with patch("os.listdir", return_value=["sysctl.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_runner.sysctl("minion", ["vm.swappiness"]) == True
                    open_mock.return_value.write.assert_has_calls(expected_calls, any_order=True)


def test_iptables(tmp_path):
    """
    test describe.iptables
    """
    iptables_ret = {
        "poc-minion": {
            "filter": {
                "INPUT": {
                    "policy": "ACCEPT",
                    "packet count": "319",
                    "byte count": "57738",
                    "rules": [
                        {"source": ["203.0.113.51/32"], "jump": ["DROP"]},
                        {
                            "protocol": ["tcp"],
                            "jump": ["ACCEPT"],
                            "in-interface": ["eth0"],
                            "match": ["tcp"],
                            "destination_port": ["22"],
                        },
                    ],
                    "rules_comment": {},
                },
                "FORWARD": {
                    "policy": "ACCEPT",
                    "packet count": "0",
                    "byte count": "0",
                    "rules": [],
                    "rules_comment": {},
                },
                "OUTPUT": {
                    "policy": "ACCEPT",
                    "packet count": "331",
                    "byte count": "33780",
                    "rules": [],
                    "rules_comment": {},
                },
            }
        }
    }

    expected_content = {
        "add_iptables_rule_0": {
            "iptables.append": [
                {"chain": "INPUT"},
                {"table": "filter"},
                {"source": "203.0.113.51/32"},
                {"jump": "DROP"},
            ]
        },
        "add_iptables_rule_1": {
            "iptables.append": [
                {"chain": "INPUT"},
                {"table": "filter"},
                {"protocol": "tcp"},
                {"jump": "ACCEPT"},
                {"in-interface": "eth0"},
                {"match": "tcp"},
                {"destination-port": "22"},
            ]
        },
    }

    iptables_sls = tmp_path / "poc-minion" / "iptables.sls"
    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=iptables_ret)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[tmp_path])},
        ):
            assert salt_describe_runner.iptables("minion") == True
            with open(iptables_sls) as fp:
                content = yaml.safe_load(fp.read())
                assert content == expected_content


def test_firewalld(tmp_path):
    """
    test describe.firewalld
    """
    firewalld_ret = {
        "poc-minion": {
            "public": {
                "target": ["default"],
                "icmp-block-inversion": ["no"],
                "interfaces": [""],
                "sources": [""],
                "services": ["dhcpv6-client ssh"],
                "ports": [""],
                "protocols": [""],
                "forward": ["yes"],
                "masquerade": ["no"],
                "forward-ports": [""],
                "source-ports": [""],
                "icmp-blocks": [""],
                "rich rules": [""],
            }
        }
    }

    expected_content = {
        "add_firewalld_rule_0": {
            "firewalld.present": [{"name": "public"}, {"services": ["dhcpv6-client", "ssh"]}]
        }
    }

    firewalld_sls = tmp_path / "poc-minion" / "firewalld.sls"
    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=firewalld_ret)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[tmp_path])},
        ):
            assert salt_describe_runner.firewalld("minion") == True
            with open(firewalld_sls) as fp:
                content = yaml.safe_load(fp.read())
                assert content == expected_content


def test_user():
    user_getent = {
        "minion": [
            {
                "name": "testuser",
                "uid": 1000,
                "gid": 1000,
                "groups": ["adm"],
                "home": "/home/testuser",
                "passwd": "x",
                "shell": "/usr/bin/zsh",
                "fullname": "",
                "homephone": "",
                "other": "",
                "roomnumber": "",
                "workphone": "",
            }
        ]
    }
    user_shadow = {
        "minion": {
            "expire": -1,
            "inact": -1,
            "lstchg": 19103,
            "max": 99999,
            "min": 0,
            "name": "testuser",
            "passwd": "$5$k69zJBp1LxA3q8az$XKEp1knAex0j.xoi/sdU4XllHpZ0JzYYRfASKGl6qZA",
            "warn": 7,
        }
    }
    fileexists = {"minion": True}
    expected_calls = [
        call().write(
            'user-testuser:\n  user.present:\n  - name: testuser\n  - uid: 1000\n  - gid: 1000\n  - allow_uid_change: true\n  - allow_gid_change: true\n  - home: /home/testuser\n  - shell: /usr/bin/zsh\n  - groups:\n    - adm\n  - password: \'{{ salt["pillar.get"]("users:testuser","*") }}\'\n  - date: 19103\n  - mindays: 0\n  - maxdays: 99999\n  - inactdays: -1\n  - expire: -1\n  - createhome: true\n'
        ),
        call().write("include:\n- minion.users\n"),
    ]

    with patch.dict(
        salt_describe_runner.__salt__,
        {"salt.execute": MagicMock(side_effect=[user_getent, user_shadow, fileexists])},
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {
                "config.get": MagicMock(
                    side_effect=[["/srv/salt"], ["/srv/salt"], ["/srv/pillar"], ["/srv/pillar"]]
                )
            },
        ):
            with patch("os.listdir", return_value=["users.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_runner.user("minion") == True
                    open_mock.return_value.write.assert_has_calls(expected_calls, any_order=True)


def test_iptables(tmp_path):
    """
    test describe.iptables
    """
    host_list = {
        "poc-minion": {
            "filter": {
                "INPUT": {
                    "policy": "ACCEPT",
                    "packet count": "319",
                    "byte count": "57738",
                    "rules": [
                        {"source": ["203.0.113.51/32"], "jump": ["DROP"]},
                        {
                            "protocol": ["tcp"],
                            "jump": ["ACCEPT"],
                            "in-interface": ["eth0"],
                            "match": ["tcp"],
                            "destination_port": ["22"],
                        },
                    ],
                    "rules_comment": {},
                },
                "FORWARD": {
                    "policy": "ACCEPT",
                    "packet count": "0",
                    "byte count": "0",
                    "rules": [],
                    "rules_comment": {},
                },
                "OUTPUT": {
                    "policy": "ACCEPT",
                    "packet count": "331",
                    "byte count": "33780",
                    "rules": [],
                    "rules_comment": {},
                },
            }
        }
    }

    expected_content = {
        "add_iptables_rule_0": {
            "iptables.append": [
                {"chain": "INPUT"},
                {"table": "filter"},
                {"source": "203.0.113.51/32"},
                {"jump": "DROP"},
            ]
        },
        "add_iptables_rule_1": {
            "iptables.append": [
                {"chain": "INPUT"},
                {"table": "filter"},
                {"protocol": "tcp"},
                {"jump": "ACCEPT"},
                {"in-interface": "eth0"},
                {"match": "tcp"},
                {"destination-port": "22"},
            ]
        },
    }

    host_file = tmp_path / "poc-minion" / "iptables.sls"
    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=host_list)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[tmp_path])},
        ):
            assert salt_describe_runner.iptables("minion") == True
            with open(host_file) as fp:
                content = yaml.safe_load(fp.read())
                assert content == expected_content


def test_all(tmp_path):
    """
    test describe.all
    """
    group_getent = {
        "minion": [
            {"gid": 4, "members": ["syslog", "vecna"], "name": "adm", "passwd": "x"},
            {"gid": 0, "members": [], "name": "root", "passwd": "x"},
        ]
    }

    pkg_list = {
        "minion": {
            "pkg1": "0.1.2-3",
            "pkg2": "1.2rc5-3",
            "pkg3": "2.3.4-5",
        }
    }

    expected_group_sls = {
        "group-adm": {
            "group.present": [{"name": "adm"}, {"gid": 4}],
        },
        "group-root": {
            "group.present": [{"name": "root"}, {"gid": 0}],
        },
    }

    expected_pkg_sls = {
        "installed_packages": {
            "pkg.installed": [{"pkgs": [{key: value} for key, value in pkg_list["minion"].items()]}]
        }
    }

    expected_init_sls = {"include": ["minion.groups", "minion.pkg"]}

    dunder_salt_mock = {
        "salt.execute": MagicMock(side_effect=[group_getent, pkg_list]),
        "describe.all": salt_describe_runner.all,
        "describe.group": salt_describe_runner.group,
        "describe.pkg": salt_describe_pkg_runner.pkg,
    }

    with patch.dict(salt_describe_runner.__salt__, dunder_salt_mock):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[str(tmp_path)])},
        ):
            with patch("os.listdir", return_value=["groups.sls", "pkg.sls"]):
                assert salt_describe_runner.all("minion", top=False) == True
                sls_files = list(tmp_path.glob("**/*.sls"))
                expected_files = ["init", "pkg", "groups"]
                expected_sls = [expected_init_sls, expected_pkg_sls, expected_group_sls]
                for filename, sls in zip(expected_files, expected_sls):
                    sls_path = tmp_path / "minion" / f"{filename}.sls"
                    assert sls_path in sls_files
                    assert yaml.safe_load(sls_path.read_text()) == sls


def test_cron(tmp_path):
    cron_ret = {
        "minion": {
            "pre": [
                '10 12 * * 4 echo "hello there!"',
                '#10 12 * * 3 echo "goodbye there!"',
                '@weekly echo "special pre cron"',
                "FENDER=STRATOCASTER",
                "# THIS= BAD",
                "",
            ],
            "crons": [
                {
                    "minute": "*",
                    "hour": "*",
                    "daymonth": "*",
                    "month": "*",
                    "dayweek": "1",
                    "identifier": "SALT_CRON_JOB",
                    "cmd": "echo foobar",
                    "comment": "-- salt lol --",
                    "commented": False,
                },
                {
                    "minute": "*",
                    "hour": "*",
                    "daymonth": "*",
                    "month": "*",
                    "dayweek": "1",
                    "identifier": "commented_cron",
                    "cmd": "echo this is commented",
                    "comment": "This is a comment on a commented cron job",
                    "commented": True,
                },
            ],
            "special": [
                {
                    "spec": "@weekly",
                    "cmd": "echo silly goose",
                    "identifier": "SILLY CRON",
                    "comment": None,
                    "commented": True,
                },
            ],
            "env": [
                {
                    "name": "SALT",
                    "value": "DESCRIBE",
                },
                {
                    "name": "HELLO",
                    "value": "to the world",
                },
            ],
        },
    }

    expected_sls = {
        "FENDER": {
            "cron.env_present": [
                {"value": "STRATOCASTER"},
                {"user": "fake_user"},
            ]
        },
        "HELLO": {
            "cron.env_present": [
                {"value": "to the world"},
                {"user": "fake_user"},
            ]
        },
        "SALT": {
            "cron.env_present": [
                {"value": "DESCRIBE"},
                {"user": "fake_user"},
            ]
        },
        'echo "goodbye there!"': {
            "cron.present": [
                {"minute": "10"},
                {"hour": "12"},
                {"daymonth": "*"},
                {"month": "*"},
                {"dayweek": "3"},
                {"comment": None},
                {"identifier": False},
                {"commented": True},
                {"user": "fake_user"},
            ]
        },
        'echo "hello there!"': {
            "cron.present": [
                {"minute": "10"},
                {"hour": "12"},
                {"daymonth": "*"},
                {"month": "*"},
                {"dayweek": "4"},
                {"comment": None},
                {"identifier": False},
                {"commented": False},
                {"user": "fake_user"},
            ]
        },
        'echo "special pre cron"': {
            "cron.present": [
                {"special": "@weekly"},
                {"comment": None},
                {"commented": False},
                {"identifier": False},
                {"user": "fake_user"},
            ]
        },
        "echo foobar": {
            "cron.present": [
                {"user": "fake_user"},
                {"minute": "*"},
                {"hour": "*"},
                {"daymonth": "*"},
                {"month": "*"},
                {"dayweek": "1"},
                {"comment": "-- salt lol --"},
                {"commented": False},
                {"identifier": "SALT_CRON_JOB"},
            ]
        },
        "echo silly goose": {
            "cron.present": [
                {"user": "fake_user"},
                {"comment": None},
                {"commented": True},
                {"identifier": "SILLY CRON"},
                {"special": "@weekly"},
            ]
        },
        "echo this is commented": {
            "cron.present": [
                {"user": "fake_user"},
                {"minute": "*"},
                {"hour": "*"},
                {"daymonth": "*"},
                {"month": "*"},
                {"dayweek": "1"},
                {"comment": "This is a comment on a commented cron job"},
                {"commented": True},
                {"identifier": "commented_cron"},
            ]
        },
    }

    user = "fake_user"
    cron_sls_file = tmp_path / "minion" / "cron.sls"

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=cron_ret)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=[tmp_path])},
        ):
            with patch("os.listdir", return_value=["cron.sls"]):
                assert salt_describe_runner.cron("minion", user) == True
                actual_sls = yaml.safe_load(cron_sls_file.read_text())
                assert actual_sls == expected_sls


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
                        assert salt_describe_runner.pkgrepo("minion") == True
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
                        assert salt_describe_runner.pkgrepo("minion") == True
                        open_mock.assert_has_calls(expected_calls, any_order=True)
