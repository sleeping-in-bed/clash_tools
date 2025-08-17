"""Tests for clash_tools.clash_tools.clash_docker CLI."""

from __future__ import annotations

import importlib
from typing import Any

import pytest
from click.testing import CliRunner


@pytest.fixture
def module() -> Any:
    return importlib.import_module("clash_tools.clash_tools.clash_docker")


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_clash_docker_cli_invokes_manager_methods(
    module: Any, runner: CliRunner, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeManager:
        def enable_proxy(self, proxy: str | None = None) -> None:  # noqa: ARG002
            calls.append("enable")

        def disable_proxy(self) -> None:
            calls.append("disable")

        def check_proxy_status(self) -> None:
            calls.append("status")

    # Patch factory used in cli() to return our fake manager
    monkeypatch.setattr(module, "DockerProxyManager", lambda: FakeManager())

    r1 = runner.invoke(module.cli, ["enable"])  # type: ignore[arg-type]
    r2 = runner.invoke(module.cli, ["disable"])  # type: ignore[arg-type]
    r3 = runner.invoke(module.cli, ["status"])  # type: ignore[arg-type]
    r4 = runner.invoke(module.cli, ["reset"])  # type: ignore[arg-type]

    assert (
        r1.exit_code == 0
        and r2.exit_code == 0
        and r3.exit_code == 0
        and r4.exit_code == 0
    )
    # reset internally calls disable_proxy, so we expect at least these methods
    assert calls[:3] == ["enable", "disable", "status"]
