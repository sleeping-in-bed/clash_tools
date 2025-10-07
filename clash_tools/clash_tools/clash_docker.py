#!/usr/bin/env python3
"""Clash Docker Proxy Management Script.

Support one-click enable and disable Docker daemon proxy settings for Clash.
"""

import os
import subprocess
from pathlib import Path

import typer

# Global default proxy settings
DEFAULT_PROXY = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
    "no_proxy": "localhost,127.0.0.1,::1",
}


class DockerProxyManager:
    def __init__(self) -> None:
        # systemd service config paths
        self.systemd_dir = Path("/etc/systemd/system/docker.service.d")
        self.systemd_proxy_file = self.systemd_dir / "http-proxy.conf"

        # Use global proxy settings
        self.proxy_settings = DEFAULT_PROXY.copy()

    def check_root(self) -> bool:
        """Check if running with root privileges."""
        return os.geteuid() == 0

    def restart_docker(self) -> bool | None:
        """Restart Docker service."""
        try:
            typer.secho("Restarting Docker service...", fg=typer.colors.BLUE)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "restart", "docker"], check=True)
            typer.secho("Docker service restarted successfully", fg=typer.colors.GREEN)
            return True
        except subprocess.CalledProcessError as e:
            typer.secho(
                f"Failed to restart Docker service: {e}",
                err=True,
                fg=typer.colors.RED,
            )
            return False

    def enable_docker_daemon_proxy(self) -> bool | None:
        """Enable Docker daemon proxy."""
        try:
            # Create systemd config directory
            self.systemd_dir.mkdir(parents=True, exist_ok=True)

            # Create proxy config file
            proxy_config = f"""[Service]
Environment="HTTP_PROXY={self.proxy_settings["http"]}"
Environment="HTTPS_PROXY={self.proxy_settings["https"]}"
Environment="NO_PROXY={self.proxy_settings["no_proxy"]}"
"""

            self.systemd_proxy_file.write_text(proxy_config, encoding="utf-8")

            typer.secho("Docker daemon proxy enabled", fg=typer.colors.GREEN)
            return True
        except Exception as e:
            typer.secho(
                f"Failed to enable Docker daemon proxy: {e}",
                err=True,
                fg=typer.colors.RED,
            )
            return False

    def disable_docker_daemon_proxy(self) -> bool | None:
        """Disable Docker daemon proxy."""
        try:
            if self.systemd_proxy_file.exists():
                self.systemd_proxy_file.unlink()
                typer.secho("Docker daemon proxy disabled", fg=typer.colors.GREEN)
            else:
                typer.secho(
                    "Docker daemon proxy config file not found, no need to disable",
                    fg=typer.colors.YELLOW,
                )
            return True
        except Exception as e:
            typer.secho(
                f"Failed to disable Docker daemon proxy: {e}",
                err=True,
                fg=typer.colors.RED,
            )
            return False

    def check_proxy_status(self) -> None:
        """Check proxy status."""
        typer.secho("=== Docker Proxy Status ===", fg=typer.colors.CYAN, bold=True)

        # Check daemon proxy
        if self.systemd_proxy_file.exists():
            typer.secho("Docker daemon proxy: Enabled", fg=typer.colors.GREEN)
            content = self.systemd_proxy_file.read_text(encoding="utf-8")
            typer.secho("   Configuration:", fg=typer.colors.CYAN)
            for line in content.strip().split("\n"):
                if line.startswith("Environment="):
                    typer.echo(f"   {line}")
        else:
            typer.secho("Docker daemon proxy: Disabled", fg=typer.colors.YELLOW)

    def enable_proxy(self, proxy_url: str | None = None) -> None:
        """Enable proxy."""
        if proxy_url:
            self.proxy_settings["http"] = proxy_url
            self.proxy_settings["https"] = proxy_url

        typer.secho("=== Enabling Docker Proxy ===", fg=typer.colors.CYAN, bold=True)
        if not self.check_root():
            typer.secho(
                "Root privileges required for Docker daemon proxy",
                fg=typer.colors.YELLOW,
            )
            typer.secho(
                "   Please run with sudo or configure daemon proxy manually",
                fg=typer.colors.YELLOW,
            )
            typer.secho("Failed to enable Docker proxy", err=True, fg=typer.colors.RED)
            return

        daemon_success = self.enable_docker_daemon_proxy()
        if daemon_success:
            self.restart_docker()
            typer.secho("Docker proxy enabled successfully!", fg=typer.colors.GREEN)
        else:
            typer.secho("Failed to enable Docker proxy", err=True, fg=typer.colors.RED)

    def disable_proxy(self) -> None:
        """Disable proxy."""
        typer.secho("=== Disabling Docker Proxy ===", fg=typer.colors.CYAN, bold=True)
        if not self.check_root():
            typer.secho(
                "Root privileges required for Docker daemon proxy",
                fg=typer.colors.YELLOW,
            )
            typer.secho(
                "   Please run with sudo or configure daemon proxy manually",
                fg=typer.colors.YELLOW,
            )
            typer.secho("Failed to disable Docker proxy", err=True, fg=typer.colors.RED)
            return

        daemon_success = self.disable_docker_daemon_proxy()
        if daemon_success:
            self.restart_docker()
            typer.secho("Docker proxy disabled successfully!", fg=typer.colors.GREEN)
        else:
            typer.secho("Failed to disable Docker proxy", err=True, fg=typer.colors.RED)


# Create Typer command group
app = typer.Typer(help="Clash Docker Proxy Management Tool")


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context) -> None:
    """Show help when no subcommand is provided, without error panel."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def enable(
    proxy: str = typer.Option(DEFAULT_PROXY["http"], "--proxy", "-p", help="Proxy URL"),
) -> None:
    r"""Enable Docker proxy.

    \b
    Examples:
        ./clash_docker enable
        ./clash_docker enable --proxy http://192.168.1.100:8080
        ./clash_docker enable -p socks5://127.0.0.1:1080
    """
    DockerProxyManager().enable_proxy(proxy)


@app.command()
def disable() -> None:
    r"""Disable Docker proxy.

    \b
    Examples:
        ./clash_docker disable
    """
    DockerProxyManager().disable_proxy()


@app.command()
def status() -> None:
    r"""Check Docker daemon proxy status.

    \b
    Examples:
        ./clash_docker status
    """
    DockerProxyManager().check_proxy_status()


@app.command()
def reset() -> None:
    r"""Reset Docker daemon proxy configuration.

    This removes the Docker daemon proxy drop-in and restarts Docker if possible.

    \b
    Examples:
        ./clash_docker reset
    """
    manager = DockerProxyManager()
    typer.secho(
        "=== Resetting Docker Proxy Configuration ===",
        fg=typer.colors.CYAN,
        bold=True,
    )
    typer.secho("This will remove:", fg=typer.colors.YELLOW)
    typer.echo("- Docker daemon proxy configuration")

    manager.disable_proxy()
    typer.secho("All configurations have been reset", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
