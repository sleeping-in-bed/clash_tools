#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Clash Runner Script
Run 'sudo ./clash -d ./' in script directory
"""

import os
import subprocess
from pathlib import Path
import click


@click.group()
def cli():
    """Clash service management tool"""
    pass


@cli.command()
def run():
    """Run 'sudo ./clash -d ./' in script directory"""
    # Get script directory
    script_dir = Path(__file__).parent.absolute()

    # Change to script directory
    original_cwd = os.getcwd()
    os.chdir(script_dir)

    click.echo(f"Running: sudo ./clash -d ./ in {script_dir}")

    # Run the command
    subprocess.run(['sudo', './clash', '-d', './'])

    # Restore original directory
    os.chdir(original_cwd)


@cli.command()
@click.option('--edit', '-e', is_flag=True, help='Open config file in default editor')
def config(edit):
    """Manage config.yaml file"""
    # Get config file path
    script_dir = Path(__file__).parent.absolute()
    config_file = script_dir / "config.yaml"

    # Always print config file path
    click.echo(f"Config file: {config_file.absolute()}")

    if not config_file.exists():
        click.echo("❌ Config file not found!", err=True)
        return

    # Handle --edit option
    if edit:
        editor = os.environ.get('EDITOR', 'nano')
        try:
            subprocess.run([editor, str(config_file)])
        except Exception as e:
            click.echo(f"❌ Error opening editor: {e}", err=True)


if __name__ == '__main__':
    cli()
