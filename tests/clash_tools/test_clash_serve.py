"""Tests for clash_tools.clash_tools.clash_serve CLI."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner


@pytest.fixture
def module() -> Any:
    return importlib.import_module("clash_tools.clash_tools.clash_serve")


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_run_invokes_sudo_clash(
    module: Any, runner: CliRunner, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool = False, **_: Any) -> None:  # noqa: ARG001
        calls.append(cmd)

    monkeypatch.setattr(
        module, "subprocess", type("S", (), {"run": staticmethod(fake_run)}),
    )

    result = runner.invoke(module.run)  # type: ignore[arg-type]
    assert result.exit_code == 0
    assert calls and calls[0][:3] == ["sudo", "./clash", "-d"]


def test_config_prints_path_and_edit_opens_editor(
    module: Any, runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    # Ensure EDITOR is a no-op
    monkeypatch.setenv("EDITOR", "true")

    # Ensure config exists
    cfg = Path(module.__file__).parent / "config.yml"
    if not cfg.exists():
        cfg.write_text("port: 7890\nsocks-port: 7891\n", encoding="utf-8")

    calls: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool = False, **_: Any) -> None:  # noqa: ARG001
        calls.append(cmd)

    monkeypatch.setattr(
        module, "subprocess", type("S", (), {"run": staticmethod(fake_run)}),
    )

    # Invoke config --edit
    result = runner.invoke(module.cli, ["config", "--edit"])  # type: ignore[arg-type]
    assert result.exit_code == 0
    # First call should be editor invocation with path
    assert calls and calls[0][0] == "true" and calls[0][1].endswith("config.yml")


def test_service_group_hint_when_not_root(
    module: Any, runner: CliRunner, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(module.os, "geteuid", lambda: 1000)
    # Avoid actually calling systemctl
    monkeypatch.setattr(
        module, "subprocess", type("S", (), {"run": staticmethod(lambda *a, **k: None)}),
    )
    # Invoke a subcommand so the group callback runs and prints the hint
    result = runner.invoke(module.cli, ["service", "status"])  # type: ignore[arg-type]
    assert result.exit_code == 0
    assert "Hint: Service commands may require sudo permissions." in result.stdout


def test_add_service_uses_run_sudo_command(
    module: Any, runner: CliRunner, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], str]] = []

    def fake_run_sudo(
        cmd: list[str],
        success_msg: str,
        failure_msg: str,
        input_data: str | None = None,
    ) -> bool | None:
        calls.append((cmd, success_msg))
        return True

    monkeypatch.setattr(module, "run_sudo_command", fake_run_sudo)

    # Ensure clash executable exists
    clash_exec = Path(module.__file__).parent / "clash"
    if not clash_exec.exists():
        clash_exec.write_bytes(b"")
        clash_exec.chmod(0o755)

    result = runner.invoke(module.add_service)  # type: ignore[arg-type]
    assert result.exit_code == 0
    # Should attempt to write service file and enable/start service
    assert any("tee" in c[0] for c in calls)
    assert any("enable" in " ".join(c[0]) for c in calls)
    assert any("start" in " ".join(c[0]) for c in calls)


def test_remove_service_with_temp_path(
    module: Any, runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    calls: list[list[str]] = []

    def fake_run_sudo(
        cmd: list[str],
        success_msg: str,
        failure_msg: str,
        input_data: str | None = None,
    ) -> bool | None:
        calls.append(cmd)
        return True

    monkeypatch.setattr(module, "run_sudo_command", fake_run_sudo)
    monkeypatch.setattr(
        module, "get_service_file_path", lambda: tmp_path / "clash.service",
    )

    # Create fake service file
    (tmp_path / "clash.service").write_text("[Unit]\n", encoding="utf-8")

    result = runner.invoke(module.remove_service)  # type: ignore[arg-type]
    assert result.exit_code == 0
    # Should call systemctl stop/disable and remove file
    joined = [" ".join(c) for c in calls]
    assert any("systemctl stop" in j for j in joined)
    assert any("systemctl disable" in j for j in joined)
    assert any(j.startswith("rm ") for j in joined)


def test_status_invokes_systemctl_status(
    module: Any, runner: CliRunner, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool = False, **_: Any) -> None:  # noqa: ARG001
        calls.append(cmd)

    monkeypatch.setattr(
        module, "subprocess", type("S", (), {"run": staticmethod(fake_run)}),
    )

    result = runner.invoke(module.status)  # type: ignore[arg-type]
    assert result.exit_code == 0
    assert calls and calls[0][:3] == ["sudo", "systemctl", "status"]
