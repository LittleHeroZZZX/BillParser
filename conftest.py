from pathlib import Path

import pytest

from billparser.config import settings

TEST_CONFIG_ROOT = Path(__file__).parent / "tests" / "config"
# skip settings.yaml to avoid cover model secrets env
all_yaml_files = [
    str(file)
    for file in TEST_CONFIG_ROOT.glob("**/*.yaml")
    if not file.name.endswith("settings.yaml")
]


@pytest.fixture(scope="session", autouse=True)
def override_dynaconf_settings():
    """Override Dynaconf settings for tests."""
    settings.load_file(all_yaml_files)
