#!/usr/bin/env python3
"""Clash proxy helper CLI using Typer."""

from pathlib import Path

import typer
import yaml

app = typer.Typer(add_completion=False)


def _config_path() -> Path:
    return Path(__file__).parent.absolute() / "config.yml"


def print_env() -> None:
    """Print environment exports for HTTP/HTTPS and SOCKS proxies."""
    config_file = _config_path()
    if not config_file.exists():
        typer.echo(f"Error: Config file not found: {config_file}", err=True)
        raise typer.Exit(code=1)

    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)

        http_port = config.get("port")
        socks_port = config.get("socks-port")

        if not http_port or not socks_port:
            typer.echo("Error: Invalid ports in config file", err=True)
            raise typer.Exit(code=1)

        typer.echo(f"export http_proxy='http://127.0.0.1:{http_port}'")
        typer.echo(f"export https_proxy='http://127.0.0.1:{http_port}'")
        typer.echo(f"export HTTP_PROXY='http://127.0.0.1:{http_port}'")
        typer.echo(f"export HTTPS_PROXY='http://127.0.0.1:{http_port}'")
        typer.echo(f"export all_proxy='socks5://127.0.0.1:{socks_port}'")
        typer.echo(f"export ALL_PROXY='socks5://127.0.0.1:{socks_port}'")
        typer.echo("export no_proxy='localhost,127.0.0.1,::1'")
        typer.echo("export NO_PROXY='localhost,127.0.0.1,::1'")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context) -> None:
    """Default behavior: print environment exports when no command is provided."""
    if ctx.invoked_subcommand is None:
        print_env()


if __name__ == "__main__":
    app()
