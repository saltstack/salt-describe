
import pytest
import saltext.salt_describe.runners.salt_describe_mod as salt_describe_runner


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"this_does_not_exist.please_replace_it": lambda: True},
    }
    return {
        salt_describe_runner: module_globals,
    }


def test_replace_this_this_with_something_meaningful():
    assert "this_does_not_exist.please_replace_it" in salt_describe_runner.__salt__
    assert salt_describe_runner.__salt__["this_does_not_exist.please_replace_it"]() is True
