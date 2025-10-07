"""Configuration helpers for wg_docker.

Provide global config directory resolution and Jinja2 environment setup.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import yaml
from jinja2 import Environment, FileSystemLoader

from .models import ServerWGConfig

_CONFIG_ENV_VAR: Final[str] = "CLASH_TOOLS_WG_CONFIG_DIR"
_DEFAULT_GLOBAL_CONFIG_DIR: Final[Path] = Path("/var/lib/clash_tools/wireguard")


def get_user_config_dir() -> Path:
    """Return the global config directory for wg_docker.

    Prefers the ``CLASH_TOOLS_WG_CONFIG_DIR`` override when present and
    otherwise uses ``/var/lib/clash_tools/wireguard``.

    Returns:
        Path: Absolute path to the configuration directory.

    """
    override = os.environ.get(_CONFIG_ENV_VAR)
    cfg_dir = Path(override) if override else _DEFAULT_GLOBAL_CONFIG_DIR
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir


def get_jinja_env() -> Environment:
    """Create and return a configured Jinja2 Environment (no autoescape)."""
    loader_dir: Path = Path(__file__).parent / "templates"
    return Environment(
        loader=FileSystemLoader(str(loader_dir)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def load_server_config() -> ServerWGConfig:
    """Load server configuration from default path in user config dir.

    If the file does not exist, bootstrap it from the packaged template.
    """
    path = get_user_config_dir() / "server_config.yml"
    if not path.exists():
        template = Path(__file__).parent / "templates" / "server_config.yml"
        path.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # Normalize clients entries: coerce null client definitions to empty dicts
    clients = data.get("clients")
    if isinstance(clients, dict):
        for k, v in list(clients.items()):
            if v is None:
                clients[k] = {}
    return ServerWGConfig(**data)
