import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.salt_describe.runners.salt_describe_service as salt_describe_service_runner
import yaml

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        salt_describe_service_runner: {
            "__salt__": {"salt.execute": MagicMock()},
            "__opts__": {},
        },
    }


def test_service():
    enabled_retval = {"minion": ["salt-master", "salt-api"]}
    disabled_retval = {"minion": ["salt-minion"]}
    status_retval = {
        "minion": {
            "salt-master": True,
            "salt-minion": True,
            "salt-api": False,
            "random-service": True
        },
    }
    
    service_sls_contents = {
        "salt-master": {
            "service.running": [{"enable": True}],
        },
        "salt-minion": {
            "service.running": [{"enable": False}],
        },
        "salt-api": {
            "service.dead": [{"enable": True}],
        },
        "random-service": {
            "service.running": [],
        },
    }
    service_sls = yaml.dump(service_sls_contents)

    execute_retvals = [enabled_retval, disabled_retval, status_retval]
    with patch.dict(salt_describe_service_runner.__salt__, {"salt.execute": MagicMock(side_effect=execute_retvals)}):
        with patch.object(salt_describe_service_runner, "generate_sls") as generate_mock:
            assert salt_describe_service_runner.service("minion") is True
            generate_mock.assert_called_with({}, "minion", service_sls, sls_name="service")
