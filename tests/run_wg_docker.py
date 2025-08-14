"""Standalone demo: generate and output WireGuard key pair.

Run this file directly to see actual results printed to stdout.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from clash_tools.wg_docker.config import get_user_config_dir, load_server_config
from clash_tools.wg_docker.utils import WGConfRenderer, WGKeyStoreManager


def main() -> int:
    """Generate keys and render server/client artifacts into tests/tmp.

    Returns:
        Exit code. 0 on success, non-zero on failure.

    """
    # Resolve config directory
    config_dir: Path = Path(__file__).parent / "tmp"

    # Patch default config path usage throughout the lib to tests/tmp
    with (
        patch(
            "clash_tools.wg_docker.config.get_user_config_dir",
            return_value=config_dir,
        ),
        patch(
            "clash_tools.wg_docker.utils.get_user_config_dir",
            return_value=config_dir,
        ),
    ):
        load_server_config()

        # Generate and persist key store (1..10 as a small demo)
        mgr = WGKeyStoreManager()
        store = mgr.generate_pairs_for_range(1, 10)
        mgr.write_store(store)

        # Read back the store (optional)
        mgr.read_store()

        # Render server wg0.conf and compose using the renderer class (includes PostUp/PostDown)
        renderer = WGConfRenderer()
        server_conf, server_out = renderer.render_server_conf()
        server_compose, server_compose_path = renderer.render_server_compose()

        # Render one client config (e.g., client id 2)
        # Generate a client_config.yml from server config/keystore (template) for client id=2
        client_cfg_yaml = renderer.get_client_conf(client_id=2)
        (config_dir / "client_config.yml").write_text(client_cfg_yaml, encoding="utf-8")

        # Render client wg0.conf and compose
        client_conf, client_out = renderer.render_client_conf()
        client_compose, client_compose_path = renderer.render_client_compose()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
