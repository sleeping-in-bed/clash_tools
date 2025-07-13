#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clash_tools package initialization
"""

import os
import sys
from pathlib import Path
import yaml
import click


@click.command()
def main():
    """
    Set up proxy environment variables based on config.yaml

    This tool reads the Clash configuration and sets up proxy environment variables.
    """
    # Output export commands for shell sourcing
    script_dir = Path(__file__).parent.absolute()
    config_file = script_dir / "config.yaml"

    if not config_file.exists():
        click.echo(f"echo '❌ Error: Config file not found: {config_file}' >&2", err=True)
        sys.exit(1)

    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        http_port = config.get('port')
        socks_port = config.get('socks-port')

        if not http_port or not socks_port:
            click.echo("echo '❌ Error: Invalid ports in config file' >&2", err=True)
            sys.exit(1)

        # Output export commands
        click.echo(f"export http_proxy='http://127.0.0.1:{http_port}'")
        click.echo(f"export https_proxy='http://127.0.0.1:{http_port}'")
        click.echo(f"export HTTP_PROXY='http://127.0.0.1:{http_port}'")
        click.echo(f"export HTTPS_PROXY='http://127.0.0.1:{http_port}'")
        click.echo(f"export all_proxy='socks5://127.0.0.1:{socks_port}'")
        click.echo(f"export ALL_PROXY='socks5://127.0.0.1:{socks_port}'")
        click.echo("export no_proxy='localhost,127.0.0.1,::1'")
        click.echo("export NO_PROXY='localhost,127.0.0.1,::1'")
        click.echo(f"echo '✅ Proxy environment variables set: HTTP/HTTPS: http://127.0.0.1:{http_port}, SOCKS: socks5://127.0.0.1:{socks_port}'")

    except Exception as e:
        click.echo(f"echo '❌ Error: {e}' >&2", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
