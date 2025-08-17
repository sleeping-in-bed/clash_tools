#!/usr/bin/env python3
"""Simple Clash Runner Script
Run 'sudo ./clash -d ./' in script directory.
"""

import os
import subprocess
from pathlib import Path

import click

SCRIPT_DIR = Path(__file__).parent.absolute()


@click.group()
def cli() -> None:
    """Clash service management tool."""


@cli.command()
def run() -> None:
    """Run 'sudo ./clash -d ./' in script directory."""
    # Change to script directory
    original_cwd = os.getcwd()
    os.chdir(SCRIPT_DIR)

    click.echo(f"Running: sudo ./clash -d ./ in {SCRIPT_DIR}")

    # Run the command
    subprocess.run(["sudo", "./clash", "-d", "./"], check=False)

    # Restore original directory
    os.chdir(original_cwd)


@cli.command()
@click.option("--edit", "-e", is_flag=True, help="Open config file in default editor")
def config(edit) -> None:
    """Manage config.yml file."""
    # Get config file path
    config_file = SCRIPT_DIR / "config.yml"

    # Always print config file path
    click.echo(f"Config file: {config_file.absolute()}")

    if not config_file.exists():
        click.echo("❌ Config file not found!", err=True)
        return

    # Handle --edit option
    if edit:
        editor = os.environ.get("EDITOR", "nano")
        try:
            subprocess.run([editor, str(config_file)], check=False)
        except Exception as e:
            click.echo(f"❌ Error opening editor: {e}", err=True)


SERVICE_NAME = "clash.service"
SYSTEMD_PATH = Path("/etc/systemd/system")


def get_service_file_path():
    """Get the path to the systemd service file."""
    return SYSTEMD_PATH / SERVICE_NAME


def run_sudo_command(command, success_msg, failure_msg, input_data=None) -> bool | None:
    """Helper to run a command with sudo and handle errors."""
    try:
        full_command = ["sudo", *command]
        subprocess.run(
            full_command,
            check=True,
            capture_output=True,
            text=True,
            input=input_data,
        )
        if success_msg:
            click.secho(f"✅ {success_msg}", fg="green")
        return True
    except subprocess.CalledProcessError as e:
        click.secho(f"❌ {failure_msg}", fg="red", err=True)
        click.secho(e.stderr.strip(), fg="red", err=True)
        return False


@click.group()
def service() -> None:
    """Manage clash as a systemd service."""
    # This check is a hint, actual sudo is enforced in run_sudo_command
    if os.geteuid() != 0:
        click.secho("Hint: Service commands may require sudo permissions.", fg="yellow")


cli.add_command(service)


@service.command("add")
def add_service() -> None:
    """Install, enable, and start the clash systemd service."""
    clash_executable = SCRIPT_DIR / "clash"
    service_file = get_service_file_path()

    if not clash_executable.is_file():
        click.secho(
            f"Clash executable not found at: {clash_executable}",
            fg="red",
            err=True,
        )
        return

    service_content = f"""[Unit]
Description=Clash Daemon
After=network.target

[Service]
Type=simple
WorkingDirectory={SCRIPT_DIR}
ExecStart={clash_executable} -d "{SCRIPT_DIR}"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    click.echo("The following service file will be created:")
    click.secho(service_content, fg="blue")

    if service_file.exists():
        click.confirm("Service file already exists. Overwrite?", abort=True)

    click.echo(f"Writing service file to {service_file}...")
    if run_sudo_command(
        ["tee", str(service_file)],
        success_msg=f"Service file created at {service_file}",
        failure_msg="Failed to create service file.",
        input_data=service_content,
    ):
        run_sudo_command(
            ["systemctl", "daemon-reload"],
            "Systemd daemon reloaded.",
            "Failed to reload systemd daemon.",
        )
        run_sudo_command(
            ["systemctl", "enable", SERVICE_NAME],
            f"Service '{SERVICE_NAME}' enabled.",
            f"Failed to enable service '{SERVICE_NAME}'.",
        )
        run_sudo_command(
            ["systemctl", "start", SERVICE_NAME],
            f"Service '{SERVICE_NAME}' started.",
            "Failed to start service.",
        )


@service.command("remove")
def remove_service() -> None:
    """Stop, disable, and remove the clash systemd service."""
    service_file = get_service_file_path()
    if not service_file.exists():
        click.secho(
            f"Service file not found at {service_file}. Is the service added?",
            fg="yellow",
        )
        return

    run_sudo_command(
        ["systemctl", "stop", SERVICE_NAME],
        f"Service '{SERVICE_NAME}' stopped.",
        "Failed to stop service.",
    )
    run_sudo_command(
        ["systemctl", "disable", SERVICE_NAME],
        f"Service '{SERVICE_NAME}' disabled.",
        "Failed to disable service.",
    )
    run_sudo_command(
        ["rm", str(service_file)],
        f"Removed service file {service_file}.",
        "Failed to remove service file.",
    )
    run_sudo_command(
        ["systemctl", "daemon-reload"],
        "Systemd daemon reloaded.",
        "Failed to reload systemd daemon.",
    )


@service.command()
def status() -> None:
    """Check the status of the clash service."""
    click.echo(f"Checking status for {SERVICE_NAME}...")
    # Does not need sudo to run, and we want to see the output directly.
    subprocess.run(["sudo", "systemctl", "status", SERVICE_NAME], check=False)


if __name__ == "__main__":
    cli()
