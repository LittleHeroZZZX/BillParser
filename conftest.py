from pathlib import Path

import pytest
from dynaconf import Dynaconf

from billparser.config import _set_settings_for_tests

TEST_CONFIG_ROOT = Path(__file__).parent / "tests" / "config"
# skip settings.yaml to avoid cover model secrets env
all_yaml_files = [str(file) for file in TEST_CONFIG_ROOT.glob("**/*.yaml")]


@pytest.fixture(scope="session", autouse=True)
def override_dynaconf_settings():
    """Override Dynaconf settings for tests."""
    settings = Dynaconf(
        envvar_prefix="BILLPARSER",
        settings_files=all_yaml_files,
        ignore_unknown_envvars=False,
        merge_enabled=True,
    )
    _set_settings_for_tests(settings)
