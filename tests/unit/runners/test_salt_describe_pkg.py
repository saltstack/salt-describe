import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.runners.salt_describe_pkg as salt_describe_pkg_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_pkg_runner: {
            "__salt__": {"salt.execute": MagicMock()},
            "__opts__": {},
        },
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
    pkg_sls_contents = {
        "installed_packages": {
            "pkg.installed": [
                {"pkgs": [{name: version} for name, version in pkg_list["minion"].items()]}
            ],
        },
    }
    pkg_sls = yaml.dump(pkg_sls_contents)
    with patch.dict(
        salt_describe_pkg_runner.__salt__, {"salt.execute": MagicMock(return_value=pkg_list)}
    ):
        with patch.object(salt_describe_pkg_runner, "generate_sls") as generate_mock:
            assert salt_describe_pkg_runner.pkg("minion") is True
            generate_mock.assert_called_with({}, "minion", pkg_sls, sls_name="pkg")
