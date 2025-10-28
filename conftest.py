from pathlib import Path

import pytest

from billparser.config import settings

TEST_CONFIG_ROOT = Path(__file__).parent / "tests" / "config"
all_yaml_files = TEST_CONFIG_ROOT.glob("**/*.yaml")


@pytest.fixture(scope="session", autouse=True)
def override_dynaconf_settings():
    """Override Dynaconf settings for tests."""
    settings.configure(
        envvar_prefix="BILLPARSER",
        settings_files=[str(file) for file in all_yaml_files],
        merge_enabled=True,
        ignore_unknown_envvars=False,
    )
