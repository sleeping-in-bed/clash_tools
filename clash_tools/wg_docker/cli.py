"""Typer-based CLI for managing WireGuard docker and configs.

Subcommands:
- server: up/down/restart/config
- client: up/down/restart/config

Config subcommand options:
- --edit: Open default editor to edit `server_config.yml`
- --cat: Print file contents
- --path: Print absolute path
- --reset: Overwrite with template copy
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import typer

from .config import get_user_config_dir
from .utils import WGConfRenderer

app = typer.Typer(help="WireGuard docker manager")
server_app = typer.Typer(help="Server operations")
client_app = typer.Typer(help="Client operations")
app.add_typer(server_app, name="server")
app.add_typer(client_app, name="client")

# Unified renderer instance
renderer = WGConfRenderer()


# ---------- Helpers ----------


def _compose_cmd(compose_file: Path, args: list[str]) -> list[str]:
    """Build docker compose command with a specific file.

    Args:
        compose_file: Path to compose YAML.
        args: Additional docker compose args.

    Returns:
        Full command list.

    """
    return ["docker", "compose", "-f", str(compose_file), *args]


def _open_in_editor(path: Path) -> None:
    """Open the file in the user's default editor."""
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nano"
    subprocess.run([editor, str(path)], check=False)


def _server_config_path() -> Path:
    """Return absolute path to server_config.yml in user config dir."""
    return get_user_config_dir() / "server_config.yml"


def _server_template() -> Path:
    """Return absolute path to the server_config.yml template in package."""
    return Path(__file__).parent / "templates" / "server_config.yml"


# ---------- Server commands ----------


@server_app.command("get-client-config")
def server_get_client_config(
    client_id: int = typer.Argument(..., help="Client id (host part)"),
) -> None:
    """Render client_config.yml for a given client id and print to stdout."""
    content = renderer.get_client_conf(client_id=client_id)
    typer.echo(content)


@server_app.command("up")
def server_up() -> None:
    """Render configs to user dir and start server docker compose in detached mode."""
    # Render server wg0.conf and compose
    renderer.render_server_conf()
    _, compose_file = renderer.render_server_compose()
    subprocess.run(_compose_cmd(compose_file, ["up", "-d"]), check=False)


@server_app.command("down")
def server_down() -> None:
    """Stop server docker compose and remove volumes."""
    _, compose_file = renderer.render_server_compose()
    subprocess.run(_compose_cmd(compose_file, ["down", "-v"]), check=False)


@server_app.command("restart")
def server_restart() -> None:
    """Restart server docker compose (down -v then up -d)."""
    server_down()
    server_up()


@server_app.command("config")
def server_config(
    edit: bool = typer.Option(
        False,
        "--edit",
        help="Edit server_config.yml in $EDITOR",
    ),
    cat: bool = typer.Option(False, "--cat", help="Print server_config.yml contents"),
    path: bool = typer.Option(
        False,
        "--path",
        help="Print server_config.yml absolute path",
    ),
    reset: bool = typer.Option(False, "--reset", help="Overwrite with template"),
) -> None:
    """Manage server_config.yml in the user config directory."""
    cfg_path = _server_config_path()

    if reset:
        template = _server_template()
        cfg_path.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        typer.secho(f"Reset from template: {cfg_path}", fg=typer.colors.GREEN)
        return

    if path:
        typer.echo(str(cfg_path.resolve()))
        return

    if cat:
        if not cfg_path.exists():
            typer.secho(
                "server_config.yml not found. Use --reset to create from template.",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=1)
        typer.echo(cfg_path.read_text(encoding="utf-8"))
        return

    if edit:
        if not cfg_path.exists():
            # bootstrap from template if missing
            template = _server_template()
            cfg_path.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        _open_in_editor(cfg_path)
        return

    # default action: show help
    raise typer.Exit(code=0)


# ---------- Client commands ----------


@client_app.command("up")
def client_up() -> None:
    """Render configs to user dir and start client docker compose in detached mode."""
    # Render client wg0.conf (default client id 2) and compose
    renderer.render_client_conf()
    _, compose_file = renderer.render_client_compose()
    subprocess.run(_compose_cmd(compose_file, ["up", "-d"]), check=False)


@client_app.command("down")
def client_down() -> None:
    """Stop client docker compose and remove volumes."""
    _, compose_file = renderer.render_client_compose()
    subprocess.run(_compose_cmd(compose_file, ["down", "-v"]), check=False)


@client_app.command("restart")
def client_restart() -> None:
    """Restart client docker compose (down -v then up -d)."""
    client_down()
    client_up()


@client_app.command("config")
def client_config(
    edit: bool = typer.Option(
        False,
        "--edit",
        help="Edit server_config.yml in $EDITOR",
    ),
    cat: bool = typer.Option(False, "--cat", help="Print server_config.yml contents"),
    path: bool = typer.Option(
        False,
        "--path",
        help="Print server_config.yml absolute path",
    ),
    reset: bool = typer.Option(False, "--reset", help="Overwrite with template"),
) -> None:
    """Mirror of server config command operating on the same server_config.yml."""
    server_config(edit=edit, cat=cat, path=path, reset=reset)


if __name__ == "__main__":
    app()
