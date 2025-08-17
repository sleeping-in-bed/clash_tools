"""Tests for clash_tools.wg_docker.cli.

Use Typer's CliRunner to invoke subcommands, isolate filesystem via
XDG_CONFIG_HOME, and monkeypatch subprocess/rendering to avoid side effects.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner


@pytest.fixture
def tmp_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide isolated XDG config directory for tests.

    Returns:
        Path: The resolved config directory base for XDG (not the app subdir).

    """
    xdg_dir: Path = tmp_path / "xdg"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_dir))
    return xdg_dir


@pytest.fixture
def cli_module(tmp_config_dir: Path) -> object:
    """Import the CLI module with isolated environment.

    Returns:
        The imported module object `clash_tools.wg_docker.cli`.

    """
    # Ensure a fresh import in case other tests import it first.
    module = importlib.import_module("clash_tools.wg_docker.cli")
    importlib.reload(module)
    return module


@pytest.fixture
def runner() -> CliRunner:
    """Return Typer's CliRunner instance."""
    return CliRunner()


@pytest.fixture
def capture_subprocess(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Capture subprocess.run invocations as a list of command lists.

    Returns:
        A mutable list that accumulates each command passed to subprocess.run.

    """
    calls: list[list[str]] = []

    def _fake_run(cmd: list[str], *, check: bool = False) -> None:
        calls.append(list(cmd))

    monkeypatch.setenv("VISUAL", "true")
    monkeypatch.setenv("EDITOR", "true")
    monkeypatch.setattr("subprocess.run", _fake_run, raising=True)
    return calls


def _app_config_path(base_xdg: Path) -> Path:
    """Resolve app server_config.yml under the test XDG config tree."""
    return base_xdg / "clash_tools" / "wireguard" / "server_config.yml"


def _compose_path(base_xdg: Path, name: str) -> Path:
    """Resolve a compose file under the test XDG config tree."""
    return base_xdg / "clash_tools" / "wireguard" / name


def _client_config_path(base_xdg: Path) -> Path:
    """Resolve client_wg0.conf under the test XDG config tree."""
    return base_xdg / "clash_tools" / "wireguard" / "client_wg0.conf"


def test_server_get_client_config_uses_renderer(
    cli_module: object,
    runner: CliRunner,
) -> None:
    """Ensure server get-client-config prints renderer output."""
    cli_module.renderer = SimpleNamespace(
        render_client_conf=lambda client_id, write=False: ("ok: 2\n", Path("ignored")),
    )
    result = runner.invoke(cli_module.app, ["server", "get-client-config", "2"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "ok: 2"


def test_server_up_invokes_compose_up(
    tmp_config_dir: Path,
    cli_module: object,
    runner: CliRunner,
    capture_subprocess: list[list[str]],
) -> None:
    """Server up should render and call docker compose up -d with file."""
    compose_path = _compose_path(tmp_config_dir, "server_compose.yml")
    cli_module.renderer = SimpleNamespace(
        render_server_conf=lambda: ("", Path("ignored")),
        render_server_compose=lambda: ("", compose_path),
    )
    result = runner.invoke(cli_module.app, ["server", "up"])
    assert result.exit_code == 0
    assert capture_subprocess == [
        ["docker", "compose", "-f", str(compose_path), "up", "-d"],
    ]


def test_server_down_invokes_compose_down(
    tmp_config_dir: Path,
    cli_module: object,
    runner: CliRunner,
    capture_subprocess: list[list[str]],
) -> None:
    """Server down should call docker compose down -v with file."""
    compose_path = _compose_path(tmp_config_dir, "server_compose.yml")
    cli_module.renderer = SimpleNamespace(
        render_server_compose=lambda: ("", compose_path),
    )
    result = runner.invoke(cli_module.app, ["server", "down"])
    assert result.exit_code == 0
    assert capture_subprocess == [
        ["docker", "compose", "-f", str(compose_path), "down", "-v"],
    ]


def test_server_restart_invokes_down_then_up(
    tmp_config_dir: Path,
    cli_module: object,
    runner: CliRunner,
    capture_subprocess: list[list[str]],
) -> None:
    """Server restart should call down then up with same compose file."""
    compose_path = _compose_path(tmp_config_dir, "server_compose.yml")
    cli_module.renderer = SimpleNamespace(
        render_server_conf=lambda: ("", Path("ignored")),
        render_server_compose=lambda: ("", compose_path),
    )
    result = runner.invoke(cli_module.app, ["server", "restart"])
    assert result.exit_code == 0
    assert capture_subprocess == [
        ["docker", "compose", "-f", str(compose_path), "down", "-v"],
        ["docker", "compose", "-f", str(compose_path), "up", "-d"],
    ]


def test_server_config_reset_and_cat_and_path(
    tmp_config_dir: Path,
    cli_module: object,
    runner: CliRunner,
) -> None:
    """Server config --reset should write template; --cat prints it; --path prints path."""
    cfg_path = _app_config_path(tmp_config_dir)

    # Reset writes the template content
    result_reset = runner.invoke(cli_module.app, ["server", "config", "--reset"])
    assert result_reset.exit_code == 0
    assert cfg_path.exists()

    template_path = cli_module._server_template()
    assert cfg_path.read_text(encoding="utf-8") == template_path.read_text(
        encoding="utf-8",
    )

    # Cat prints the content
    result_cat = runner.invoke(cli_module.app, ["server", "config", "--cat"])
    assert result_cat.exit_code == 0
    assert result_cat.stdout == cfg_path.read_text(encoding="utf-8") + "\n"

    # Path prints the resolved path
    result_path = runner.invoke(cli_module.app, ["server", "config", "--path"])
    assert result_path.exit_code == 0
    assert result_path.stdout.strip() == str(cfg_path.resolve())


def test_server_config_cat_missing_file_exits_with_error(
    tmp_config_dir: Path,
    runner: CliRunner,
) -> None:
    """Server config --cat when config file is missing should exit 1."""
    module = importlib.import_module("clash_tools.wg_docker.cli")
    importlib.reload(module)
    cfg_path = _app_config_path(tmp_config_dir)
    if cfg_path.exists():
        cfg_path.unlink()
    result = runner.invoke(module.app, ["server", "config", "--cat"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()


def test_client_up_down_restart(
    tmp_config_dir: Path,
    cli_module: object,
    runner: CliRunner,
    capture_subprocess: list[list[str]],
) -> None:
    """Client up/down/restart should use compose file and invoke docker compose."""
    compose_path = _compose_path(tmp_config_dir, "client_compose.yml")
    cli_module.renderer = SimpleNamespace(
        render_client_conf=lambda client_id=2: ("", Path("ignored")),
        render_client_compose=lambda: ("", compose_path),
    )

    r1 = runner.invoke(cli_module.app, ["client", "up"])
    r2 = runner.invoke(cli_module.app, ["client", "down"])
    # restart
    r3 = runner.invoke(cli_module.app, ["client", "restart"])

    assert r1.exit_code == 0 and r2.exit_code == 0 and r3.exit_code == 0

    expected = [
        ["docker", "compose", "-f", str(compose_path), "up", "-d"],
        ["docker", "compose", "-f", str(compose_path), "down", "-v"],
        ["docker", "compose", "-f", str(compose_path), "down", "-v"],
        ["docker", "compose", "-f", str(compose_path), "up", "-d"],
    ]
    assert capture_subprocess == expected


def test_client_config_path_is_client_yaml(
    tmp_config_dir: Path,
    cli_module: object,
    runner: CliRunner,
) -> None:
    """Client config --path should point to client_wg0.conf."""
    expected_client_path = _client_config_path(tmp_config_dir)
    res_client = runner.invoke(cli_module.app, ["client", "config", "--path"])
    assert res_client.exit_code == 0
    assert res_client.stdout.strip() == str(expected_client_path)


def test_server_config_edit_bootstrap_opens_editor(
    tmp_config_dir: Path,
    cli_module: object,
    runner: CliRunner,
    capture_subprocess: list[list[str]],
) -> None:
    """Server config --edit should create file if missing and open editor."""
    cfg_path = _app_config_path(tmp_config_dir)
    if cfg_path.exists():
        cfg_path.unlink()

    result = runner.invoke(cli_module.app, ["server", "config", "--edit"])
    assert result.exit_code == 0
    assert cfg_path.exists()
    # The first captured subprocess call should be opening the editor
    assert capture_subprocess == [["true", str(cfg_path)]]


def test_client_config_reset_and_cat(
    tmp_config_dir: Path,
    cli_module: object,
    runner: CliRunner,
) -> None:
    """Client config --reset creates file; --cat prints its content (empty by default)."""
    cfg_path = _client_config_path(tmp_config_dir)

    res_reset = runner.invoke(cli_module.app, ["client", "config", "--reset"])
    assert res_reset.exit_code == 0
    assert cfg_path.exists()

    res_cat = runner.invoke(cli_module.app, ["client", "config", "--cat"])
    assert res_cat.exit_code == 0
    assert res_cat.stdout == "\n"
