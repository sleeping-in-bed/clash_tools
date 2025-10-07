#!/usr/bin/env python3
"""Simple Clash Runner Script using Typer.

Run 'sudo ./clash -d <user_config_dir>' with config managed under the user's
XDG config directory.
"""

import os
import subprocess
from pathlib import Path

import typer

from clash_tools.clash_tools.config import (
    SCRIPT_DIR,
    ensure_country_mmdb,
    template_config_path,
    user_config_dir,
    user_config_path,
)

app = typer.Typer(help="Clash service management tool")
service_app = typer.Typer(
    help="Manage clash as a systemd service",
)
app.add_typer(service_app, name="service")


@app.command()
def run() -> None:
    """Run clash using the user config directory."""
    cfg_dir = user_config_dir()
    # Ensure Country.mmdb exists in user config directory
    ensure_country_mmdb()
    typer.secho(
        f"Running: sudo {SCRIPT_DIR / 'clash'!s} -d {cfg_dir}",
        fg=typer.colors.CYAN,
        bold=True,
    )
    # Execute from script dir where binary resides, but point -d to user cfg dir
    subprocess.run(["sudo", str(SCRIPT_DIR / "clash"), "-d", str(cfg_dir)], check=False)


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context) -> None:
    """Show help when no subcommand is provided, without error panel."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def config(
    edit: bool = typer.Option(
        False,
        "--edit",
        "-e",
        help="Open config file in default editor",
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        help="Overwrite user config from template",
    ),
) -> None:
    """Manage user config.yaml file.

    - Always prints the user config path
    - If --reset is provided, copy template to user config (overwrite)
    - If --edit is provided, ensure user config exists by copying template if missing, then open editor
    """
    user_cfg = user_config_path()
    tpl_cfg = template_config_path()

    typer.secho(f"Config file: {user_cfg.absolute()}", fg=typer.colors.CYAN)

    if reset:
        if not tpl_cfg.exists():
            typer.secho("Template config not found!", err=True, fg=typer.colors.RED)
            return
        ok = run_sudo_command(
            ["cp", str(tpl_cfg), str(user_cfg)],
            success_msg="",
            failure_msg="Failed to reset from template.",
        )
        if ok:
            typer.secho("Reset from template.", fg=typer.colors.GREEN)
        return

    if edit:
        # bootstrap from template if missing
        if not user_cfg.exists():
            if tpl_cfg.exists():
                run_sudo_command(
                    ["cp", str(tpl_cfg), str(user_cfg)],
                    success_msg="",
                    failure_msg="Failed to bootstrap config from template.",
                )
            else:
                # create empty file if template missing
                run_sudo_command(
                    ["touch", str(user_cfg)],
                    success_msg="",
                    failure_msg="Failed to create empty config file.",
                )
        editor = os.environ.get("EDITOR", "nano")
        try:
            subprocess.run(["sudo", editor, str(user_cfg)], check=False)
        except Exception as e:
            typer.secho(f"Error opening editor: {e}", err=True, fg=typer.colors.RED)
        return


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
            typer.echo(success_msg)
        return True
    except subprocess.CalledProcessError as e:
        typer.echo(failure_msg, err=True)
        typer.echo(e.stderr.strip(), err=True)
        return False


@service_app.callback()
def service() -> None:
    """Manage clash as a systemd service."""
    # This check is a hint, actual sudo is enforced in run_sudo_command
    if os.geteuid() != 0:
        typer.secho(
            "Hint: Service commands may require sudo permissions.",
            fg=typer.colors.YELLOW,
        )


@service_app.command("add")
def add_service() -> None:
    """Install, enable, and start the clash systemd service."""
    clash_executable = SCRIPT_DIR / "clash"
    service_file = get_service_file_path()

    if not clash_executable.is_file():
        typer.secho(
            f"Clash executable not found at: {clash_executable}",
            err=True,
            fg=typer.colors.RED,
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
    typer.secho("The following service file will be created:", fg=typer.colors.CYAN)
    typer.echo(service_content)

    if service_file.exists():
        if not typer.confirm("Service file already exists. Overwrite?"):
            raise typer.Abort()

    typer.secho(f"Writing service file to {service_file}...", fg=typer.colors.CYAN)
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


@service_app.command("remove")
def remove_service() -> None:
    """Stop, disable, and remove the clash systemd service."""
    service_file = get_service_file_path()
    if not service_file.exists():
        typer.echo(f"Service file not found at {service_file}. Is the service added?")
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


@service_app.command()
def status() -> None:
    """Check the status of the clash service."""
    typer.echo(f"Checking status for {SERVICE_NAME}...")
    # Does not need sudo to run, and we want to see the output directly.
    subprocess.run(["sudo", "systemctl", "status", SERVICE_NAME], check=False)


if __name__ == "__main__":
    app()
