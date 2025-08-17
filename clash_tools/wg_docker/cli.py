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
from .utils import WGConfRenderer, WGKeyStoreManager

app = typer.Typer(help="WireGuard docker manager", no_args_is_help=True)
server_app = typer.Typer(help="Server operations", no_args_is_help=True)
client_app = typer.Typer(help="Client operations", no_args_is_help=True)
app.add_typer(server_app, name="server")
app.add_typer(client_app, name="client")


def _ensure_keystore() -> None:
    """Ensure wg_keys.json exists; generate 1..254 if missing.

    This avoids runtime failures when rendering configs on fresh hosts.
    """
    mgr = WGKeyStoreManager()
    if mgr.json_path.exists():
        return
    store = mgr.generate_pairs_for_range()
    mgr.write_store(store)


# Ensure keystore before creating renderer singleton
_ensure_keystore()

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


def _client_config_path() -> Path:
    """Return absolute path to client_wg0.conf in user config dir."""
    return get_user_config_dir() / "client_wg0.conf"


def _server_template() -> Path:
    """Return absolute path to the server_config.yml template in package."""
    return Path(__file__).parent / "templates" / "server_config.yml"


# ---------- Server commands ----------


@server_app.command("get-client-config")
def server_get_client_config(
    client_id: int = typer.Argument(..., help="Client id (host part)"),
) -> None:
    """Render client_wg0.conf for a given client id and print to stdout."""
    rendered, _ = renderer.render_client_conf(client_id=client_id, write=False)
    typer.echo(rendered)


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


@server_app.command("show")
def server_show() -> None:
    """Exec into the server container and run `wg show`."""
    _, compose_file = renderer.render_server_compose()
    subprocess.run(
        _compose_cmd(compose_file, ["exec", "wireguard", "wg", "show"]),
        check=False,
    )


def _do_config_yml(
    *,
    cfg_path: Path,
    template: Path | None,
    edit: bool,
    cat: bool,
    show_path: bool,
    reset: bool,
) -> None:
    """Generic config file manager for YAML files in user config dir."""
    if reset:
        if template is not None:
            cfg_path.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            # Create empty file if no template provided
            cfg_path.write_text("", encoding="utf-8")
        typer.secho(f"Reset: {cfg_path}", fg=typer.colors.GREEN)
        return

    if show_path:
        typer.echo(str(cfg_path.resolve()))
        return

    if cat:
        if not cfg_path.exists():
            typer.secho(
                f"{cfg_path.name} not found. Use --reset to create.",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=1)
        typer.echo(cfg_path.read_text(encoding="utf-8"))
        return

    if edit:
        if not cfg_path.exists():
            if template is not None:
                cfg_path.write_text(
                    template.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            else:
                cfg_path.write_text("", encoding="utf-8")
        _open_in_editor(cfg_path)
        return

    # default action: show help
    raise typer.Exit(code=0)


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
    _do_config_yml(
        cfg_path=_server_config_path(),
        template=_server_template(),
        edit=edit,
        cat=cat,
        show_path=path,
        reset=reset,
    )


# ---------- Client commands ----------


@client_app.command("up")
def client_up() -> None:
    """Render configs to user dir and start client docker compose in detached mode."""
    # Only render client compose; client_wg0.conf is managed via `client config`
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
        help="Edit client_wg0.conf in $EDITOR",
    ),
    cat: bool = typer.Option(False, "--cat", help="Print client_wg0.conf contents"),
    path: bool = typer.Option(
        False,
        "--path",
        help="Print client_wg0.conf absolute path",
    ),
    reset: bool = typer.Option(False, "--reset", help="Create empty file if missing"),
) -> None:
    """Manage client_wg0.conf in the user config directory."""
    _do_config_yml(
        cfg_path=_client_config_path(),
        template=None,
        edit=edit,
        cat=cat,
        show_path=path,
        reset=reset,
    )


if __name__ == "__main__":
    app()
