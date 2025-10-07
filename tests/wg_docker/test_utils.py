"""Tests for WireGuard utilities."""

from __future__ import annotations

from subprocess import CompletedProcess
from typing import TYPE_CHECKING

import pytest

from clash_tools.wg_docker.config import load_server_config
from clash_tools.wg_docker.utils import (
    WGConfRenderer,
    WGKeyPair,
    WGKeyStore,
    WGKeyStoreManager,
    generate_wg_keypair,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def _override_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests run against an isolated config directory."""
    monkeypatch.setenv("CLASH_TOOLS_WG_CONFIG_DIR", str(tmp_path))


def test_generate_wg_keypair_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return a WGKeyPair when underlying `wg` commands succeed."""

    def fake_run(
        args: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
        input: str | None = None,
        **_: object,
    ) -> CompletedProcess[str]:
        if args == ["wg", "genkey"]:
            return CompletedProcess(
                args=args,
                returncode=0,
                stdout="PRIVKEY\n",
                stderr="",
            )
        if args == ["wg", "pubkey"]:
            assert input == "PRIVKEY"  # ensure private key is piped into pubkey
            return CompletedProcess(
                args=args,
                returncode=0,
                stdout="PUBKEY\n",
                stderr="",
            )
        msg = f"unexpected command: {args}"
        raise AssertionError(msg)

    monkeypatch.setattr("clash_tools.wg_docker.utils.run", fake_run)

    result: WGKeyPair = generate_wg_keypair()
    assert isinstance(result, WGKeyPair)
    assert result.private_key == "PRIVKEY"  # pragma: allowlist secret
    assert result.public_key == "PUBKEY"


def test_generate_wg_keypair_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise RuntimeError when the `wg` command is unavailable or fails."""

    def fake_run_fail(*_: object, **__: object) -> CompletedProcess[str]:
        msg = "wg not found"
        raise FileNotFoundError(msg)

    monkeypatch.setattr("clash_tools.wg_docker.utils.run", fake_run_fail)

    with pytest.raises(RuntimeError):
        generate_wg_keypair()


def test_load_server_config_uses_default_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Load config from default dir by patching get_user_config_dir to tmp_path."""
    cfg_text = """
server:
  server_ip: 203.0.113.10
  subnet: 10.99.0.0/24
  listen_port: 51820
clients:
  2:
    snat: true
    c_to_s_ports:
      - [22, 2222]
""".strip()
    # Patch config dir for config.load_server_config
    monkeypatch.setattr(
        "clash_tools.wg_docker.config.get_user_config_dir",
        lambda: tmp_path,
    )
    (tmp_path / "server_config.yml").write_text(cfg_text, encoding="utf-8")

    cfg = load_server_config()
    assert cfg.server.subnet == "10.99.0.0/24"
    assert cfg.server.listen_port == 51820
    assert cfg.server.server_ip == "203.0.113.10"


def _write_store(tmp_path: Path) -> None:
    manager = WGKeyStoreManager()
    store = WGKeyStore(
        pairs={
            1: WGKeyPair(private_key="S_PRIV", public_key="S_PUB"),
            2: WGKeyPair(private_key="C2_PRIV", public_key="C2_PUB"),
        },
    )
    manager.write_store(store)


def test_renderer_build_rules_and_render(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build PostUp/PostDown and render server & client configs."""
    # Patch both config and utils to use tmp_path as config dir
    monkeypatch.setattr(
        "clash_tools.wg_docker.config.get_user_config_dir",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        "clash_tools.wg_docker.utils.get_user_config_dir",
        lambda: tmp_path,
    )

    # Write config
    cfg_text = """
server:
  server_ip: 203.0.113.10
  subnet: 10.99.0.0/24
  listen_port: 51820
clients:
  2:
    snat: true
    c_to_s_ports:
      - [22, 2222]
""".strip()
    (tmp_path / "server_config.yml").write_text(cfg_text, encoding="utf-8")

    # Write keystore
    _write_store(tmp_path)

    renderer = WGConfRenderer()

    post_up, post_down = renderer._build_server_post()
    # Baseline
    assert any("-A FORWARD -i %i -j ACCEPT" in r for r in post_up)
    assert any("-t nat -A POSTROUTING -o eth0 -j MASQUERADE" in r for r in post_up)
    # DNAT/FORWARD for mapping
    assert any(
        "-t nat -A PREROUTING -p tcp --dport 2222 -j DNAT --to-destination 10.99.0.2:22"
        in r
        for r in post_up
    )
    assert any(
        "-A FORWARD -p tcp -d 10.99.0.2 --dport 22 -j ACCEPT" in r for r in post_up
    )
    # SNAT added because snat=true
    assert any(
        "-t nat -A POSTROUTING -o wg0 -p tcp -d 10.99.0.2 --dport 22 -j SNAT --to-source 10.99.0.1"
        in r
        for r in post_up
    )
    # Down rules mirror
    assert any(
        "-t nat -D PREROUTING -p tcp --dport 2222 -j DNAT --to-destination 10.99.0.2:22"
        in r
        for r in post_down
    )

    # Render server config (no write)
    server_conf, _ = renderer.render_server_conf(write=False)
    assert "[Interface]" in server_conf
    assert "Address = 10.99.0.1/24" in server_conf
    assert "ListenPort = 51820" in server_conf
    assert "PublicKey = C2_PUB" in server_conf
    assert "AllowedIPs = 10.99.0.2/32" in server_conf
    assert "PostUp = " in server_conf

    # Render client wg0.conf from server-side config for id=2
    client_conf, _ = renderer.render_client_conf(client_id=2, write=False)
    assert "[Interface]" in client_conf
    assert "Address = 10.99.0.2/32" in client_conf
    assert "PrivateKey = C2_PRIV" in client_conf
    assert "PublicKey = S_PUB" in client_conf
    assert "Endpoint = 203.0.113.10:51820" in client_conf
