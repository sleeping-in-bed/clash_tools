"""Tests for clash_tools.clash_tools.clash_docker CLI."""

from __future__ import annotations

import importlib

import pytest
from typer.testing import CliRunner


@pytest.fixture
def module() -> object:
    """Import the clash_docker module."""
    return importlib.import_module("clash_tools.clash_tools.clash_docker")


@pytest.fixture
def runner() -> CliRunner:
    """Return a CliRunner instance."""
    return CliRunner()


def test_clash_docker_cli_invokes_manager_methods(
    module: object,
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that CLI commands invoke the correct manager methods."""
    calls: list[str] = []

    class FakeManager:
        def enable_proxy(self, proxy: str | None = None) -> None:
            calls.append("enable")

        def disable_proxy(self) -> None:
            calls.append("disable")

        def check_proxy_status(self) -> None:
            calls.append("status")

    # Patch manager creation to our fake
    monkeypatch.setattr(module, "DockerProxyManager", FakeManager)

    r1 = runner.invoke(module.app, ["enable"])
    r2 = runner.invoke(module.app, ["disable"])
    r3 = runner.invoke(module.app, ["status"])
    r4 = runner.invoke(module.app, ["reset"])

    assert (
        r1.exit_code == 0
        and r2.exit_code == 0
        and r3.exit_code == 0
        and r4.exit_code == 0
    )
    # reset internally calls disable_proxy, so we expect at least these methods
    assert calls[:3] == ["enable", "disable", "status"]
