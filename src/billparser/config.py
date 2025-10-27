from pathlib import Path

from dynaconf import Dynaconf

ROOT_DIR = Path(__file__).parent.parent.parent
CONFIG_ROOT = ROOT_DIR / "config"
all_yaml_files = CONFIG_ROOT.glob("**/*.yaml")
to_load_yaml_files = [
    str(file) for file in all_yaml_files if not file.name.endswith(".example.yaml")
]
if not to_load_yaml_files:
    to_load_yaml_files = [str(CONFIG_ROOT / "settings.yaml")]

settings = Dynaconf(
    envvar_prefix="BILLPARSER",
    settings_files=to_load_yaml_files,
    ignore_unknown_envvars=True,
    merge_enabled=True,
)
