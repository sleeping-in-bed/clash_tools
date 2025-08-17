"""Tests for clash_tools.clash_tools.clash_serve CLI."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from typer.testing import CliRunner


@pytest.fixture
def module() -> object:
    """Import the clash_serve module."""
    return importlib.import_module("clash_tools.clash_tools.clash_serve")


@pytest.fixture
def runner() -> CliRunner:
    """Return a CliRunner instance."""
    return CliRunner()


def test_run_invokes_sudo_clash(
    module: object,
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that `run` command invokes `sudo clash`."""
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, check: bool = False, **_: object) -> None:
        calls.append(cmd)

    monkeypatch.setattr(
        module,
        "subprocess",
        type("S", (), {"run": staticmethod(fake_run)}),
    )

    # Invoke via app to use typer runner correctly
    result = runner.invoke(module.app, ["run"])
    assert result.exit_code == 0
    assert calls and calls[0][0] == "sudo" and calls[0][2] == "-d"


def test_config_prints_path_and_edit_opens_editor(
    module: object,
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test that `config` prints path and `config --edit` opens editor."""
    # Ensure EDITOR is a no-op
    monkeypatch.setenv("EDITOR", "true")

    # Ensure template exists
    tpl = Path(module.__file__).parent / "config.yaml"
    if not tpl.exists():
        tpl.write_text("port: 7890\nsocks-port: 7891\n", encoding="utf-8")

    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, check: bool = False, **_: object) -> None:
        calls.append(cmd)

    monkeypatch.setattr(
        module,
        "subprocess",
        type("S", (), {"run": staticmethod(fake_run)}),
    )

    # Invoke config --edit
    result = runner.invoke(module.app, ["config", "--edit"])
    assert result.exit_code == 0
    # First call should be editor invocation with path
    assert calls and calls[0][0] == "true" and calls[0][1].endswith("config.yaml")


def test_service_group_hint_when_not_root(
    module: object,
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(module.os, "geteuid", lambda: 1000)
    # Avoid actually calling systemctl
    monkeypatch.setattr(
        module,
        "subprocess",
        type("S", (), {"run": staticmethod(lambda *a, **k: None)}),
    )
    # Invoke a subcommand so the callback runs and prints the hint
    result = runner.invoke(module.app, ["service", "status"])
    assert result.exit_code == 0
    assert "Hint: Service commands may require sudo permissions." in result.stdout


def test_add_service_uses_run_sudo_command(
    module: object,
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that `add-service` uses the run_sudo_command helper."""
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

    result = runner.invoke(module.app, ["service", "add"])
    assert result.exit_code == 0
    # Should attempt to write service file and enable/start service
    assert any("tee" in c[0] for c in calls)
    assert any("enable" in " ".join(c[0]) for c in calls)
    assert any("start" in " ".join(c[0]) for c in calls)


def test_remove_service_with_temp_path(
    module: object,
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test `remove-service` command with a temporary service file."""
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
        module,
        "get_service_file_path",
        lambda: tmp_path / "clash.service",
    )

    # Create fake service file
    (tmp_path / "clash.service").write_text("[Unit]\n", encoding="utf-8")

    result = runner.invoke(module.app, ["service", "remove"])
    assert result.exit_code == 0
    # Should call systemctl stop/disable and remove file
    joined = [" ".join(c) for c in calls]
    assert any("systemctl stop" in j for j in joined)
    assert any("systemctl disable" in j for j in joined)
    assert any(j.startswith("rm ") for j in joined)


def test_status_invokes_systemctl_status(
    module: object,
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that `status` command invokes `systemctl status`."""
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *, check: bool = False, **_: object) -> None:
        calls.append(cmd)

    monkeypatch.setattr(
        module,
        "subprocess",
        type("S", (), {"run": staticmethod(fake_run)}),
    )

    result = runner.invoke(module.app, ["service", "status"])
    assert result.exit_code == 0
    assert calls and calls[0][:3] == ["sudo", "systemctl", "status"]
