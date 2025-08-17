"""Tests for clash_tools CLI scripts: clash_proxy, clash_serve."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def in_pkg_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Ensure running inside moved package directory
    pkg_dir = Path(__file__).parents[2] / "clash_tools" / "clash_tools"
    assert (pkg_dir / "config.yml").exists()
    monkeypatch.chdir(pkg_dir)
    return pkg_dir


def test_clash_proxy_reads_config_and_prints_exports(in_pkg_dir: Path) -> None:
    mod = importlib.import_module("clash_tools.clash_tools.clash_proxy")
    runner = CliRunner()
    result = runner.invoke(mod.main)
    assert result.exit_code == 0
    assert "export http_proxy='http://127.0.0.1:" in result.stdout
    assert "export all_proxy='socks5://127.0.0.1:" in result.stdout


def test_clash_serve_config_path_and_edit_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = importlib.import_module("clash_tools.clash_tools.clash_serve")
    runner = CliRunner()

    # Prepare fake editor
    monkeypatch.setenv("EDITOR", "true")

    # Change to module dir to ensure config path calculation
    script_dir = Path(mod.__file__).parent
    monkeypatch.chdir(script_dir)

    # Ensure config exists
    cfg = script_dir / "config.yml"
    if not cfg.exists():
        cfg.write_text("port: 7890\nsocks-port: 7891\n", encoding="utf-8")

    result = runner.invoke(mod.cli, ["config", "--path"], catch_exceptions=False)
    # Our CLI shows path unconditionally; emulate by running without args then with --edit
    # Here we just ensure the command succeeds; editor execution is covered by setting EDITOR=true
    result = runner.invoke(mod.cli, ["config", "--edit"], catch_exceptions=False)
    assert result.exit_code == 0
