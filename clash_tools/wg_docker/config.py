"""Configuration helpers for wg_docker.

Provide user config directory resolution and Jinja2 environment setup.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from .models import ServerWGConfig


def get_user_config_dir() -> Path:
    """Return the user config directory for wg_docker, respecting XDG.

    Follows: `$XDG_CONFIG_HOME` if set, otherwise `~/.config`, then
    `clash_tools/wireguard`.

    Returns:
        Path to the configuration directory.

    """
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    base_config_dir = (
        Path(xdg_config_home) if xdg_config_home else Path.home() / ".config"
    )
    cfg_dir = base_config_dir / "clash_tools" / "wireguard"
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
