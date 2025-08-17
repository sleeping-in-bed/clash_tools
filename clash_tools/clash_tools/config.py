"""Configuration path utilities for clash_tools.

Provide helpers to resolve the script directory, user configuration directory,
and the paths to the user and template configuration files.

All paths are XDG compliant where applicable.
"""

from __future__ import annotations

import os
from pathlib import Path
from shutil import copyfile

SCRIPT_DIR: Path = Path(__file__).parent.absolute()


def user_config_dir() -> Path:
    """Return user config directory for Clash (XDG compliant)."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    cfg_dir = base / "clash_tools" / "clash"
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
