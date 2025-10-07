"""Configuration path utilities for clash_tools.

Provide helpers to resolve the script directory, global configuration directory,
and the paths to the configuration files.
"""

from __future__ import annotations

import os
from pathlib import Path
from shutil import copyfile
from typing import Final

SCRIPT_DIR: Path = Path(__file__).parent.absolute()
_CONFIG_ENV_VAR: Final[str] = "CLASH_TOOLS_CONFIG_DIR"
_DEFAULT_GLOBAL_CONFIG_DIR: Final[Path] = Path("/var/lib/clash_tools/clash")


def user_config_dir() -> Path:
    """Return the global config directory for Clash.

    Prefers the ``CLASH_TOOLS_CONFIG_DIR`` override when provided and
    otherwise falls back to ``/var/lib/clash_tools/clash``.

    Returns:
        Path: Absolute path to the configuration directory.

    """
    override = os.environ.get(_CONFIG_ENV_VAR)
    cfg_dir = Path(override) if override else _DEFAULT_GLOBAL_CONFIG_DIR
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir


def user_config_path() -> Path:
    """Return user config file path (config.yaml)."""
    return user_config_dir() / "config.yaml"


def template_config_path() -> Path:
    """Return template config path shipped with the package (in SCRIPT_DIR)."""
    return SCRIPT_DIR / "config.yaml"


def ensure_country_mmdb() -> None:
    """Ensure Country.mmdb exists in the user config directory.

    Copies it from SCRIPT_DIR if present and not already in the user config.
    """
    cfg_dir = user_config_dir()
    mmdb_src = SCRIPT_DIR / "Country.mmdb"
    mmdb_dst = cfg_dir / "Country.mmdb"
    if mmdb_src.exists() and not mmdb_dst.exists():
        copyfile(mmdb_src, mmdb_dst)
