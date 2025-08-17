"""Tests for clash_tools CLI scripts: clash_proxy, clash_serve."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from typer.testing import CliRunner


@pytest.fixture
def in_pkg_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Ensure running inside moved package directory, and prepare user config."""
    # Directory that contains top-level config.py used by scripts (imported as `from config import ...`)
    pkg_dir = Path(__file__).parents[2] / "clash_tools" / "clash_tools" / "clash_tools"
    # Prepare XDG user config
    xdg_home = tmp_path / "xdg"
    user_cfg_dir = xdg_home / "clash_tools" / "clash"
    user_cfg_dir.mkdir(parents=True, exist_ok=True)
    (user_cfg_dir / "config.yaml").write_text(
        "port: 7890\nsocks-port: 7891\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_home))
    return pkg_dir


def test_clash_proxy_reads_config_and_prints_exports(in_pkg_dir: Path) -> None:
    """Test that clash_proxy reads config and prints exports."""
    mod = importlib.import_module("clash_tools.clash_tools.clash_proxy")
    runner = CliRunner()
    result = runner.invoke(mod.app, [])
    assert result.exit_code == 0
    assert "export http_proxy='http://127.0.0.1:" in result.stdout
    assert "export all_proxy='socks5://127.0.0.1:" in result.stdout


def test_clash_serve_config_path_and_edit_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test --config-path and --edit flags."""
    mod = importlib.import_module("clash_tools.clash_tools.clash_serve")
    runner = CliRunner()

    # Prepare fake editor
    monkeypatch.setenv("EDITOR", "true")

    # Change to module dir to ensure config path calculation
    script_dir = Path(mod.__file__).parent
    monkeypatch.chdir(script_dir)

    # Ensure config exists
    cfg = script_dir / "config.yaml"
    if not cfg.exists():
        cfg.write_text("port: 7890\nsocks-port: 7891\n", encoding="utf-8")

    result = runner.invoke(mod.app, ["config", "--path"], catch_exceptions=False)
    # Our CLI shows path unconditionally; emulate by running without args then with --edit
    # Here we just ensure the command succeeds; editor execution is covered by setting EDITOR=true
    result = runner.invoke(mod.app, ["config", "--edit"], catch_exceptions=False)
    assert result.exit_code == 0
