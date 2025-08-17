#!/usr/bin/env python3
"""Clash Docker Proxy Management Script
Support one-click enable and disable Docker proxy settings for Clash.
"""

import json
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
        # Docker config file paths
        self.docker_config_dir = Path.home() / ".docker"
        self.docker_config_file = self.docker_config_dir / "config.json"

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
            typer.echo("Restarting Docker service...")
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "restart", "docker"], check=True)
            typer.echo("Docker service restarted successfully")
            return True
        except subprocess.CalledProcessError as e:
            typer.echo(f"Failed to restart Docker service: {e}", err=True)
            return False

    def enable_docker_client_proxy(self) -> bool | None:
        """Enable Docker client proxy."""
        try:
            # Create config directory
            self.docker_config_dir.mkdir(exist_ok=True)

            # Read existing config
            config = {}
            if self.docker_config_file.exists():
                with open(self.docker_config_file) as f:
                    config = json.load(f)

            # Add proxy configuration
            config["proxies"] = {
                "default": {
                    "httpProxy": self.proxy_settings["http"],
                    "httpsProxy": self.proxy_settings["https"],
                    "noProxy": self.proxy_settings["no_proxy"],
                },
            }

            # Write config file
            with open(self.docker_config_file, "w") as f:
                json.dump(config, f, indent=2)

            typer.echo("Docker client proxy enabled")
            return True
        except Exception as e:
            typer.echo(f"Failed to enable Docker client proxy: {e}", err=True)
            return False

    def disable_docker_client_proxy(self) -> bool | None:
        """Disable Docker client proxy."""
        try:
            if not self.docker_config_file.exists():
                typer.echo(
                    "Docker client proxy config file not found, no need to disable",
                )
                return True

            # Read existing config
            with open(self.docker_config_file) as f:
                config = json.load(f)

            # Remove proxy configuration
            if "proxies" in config:
                del config["proxies"]

            # Write config file
            with open(self.docker_config_file, "w") as f:
                json.dump(config, f, indent=2)

            typer.echo("Docker client proxy disabled")
            return True
        except Exception as e:
            typer.echo(f"Failed to disable Docker client proxy: {e}", err=True)
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

            with open(self.systemd_proxy_file, "w") as f:
                f.write(proxy_config)

            typer.echo("Docker daemon proxy enabled")
            return True
        except Exception as e:
            typer.echo(f"Failed to enable Docker daemon proxy: {e}", err=True)
            return False

    def disable_docker_daemon_proxy(self) -> bool | None:
        """Disable Docker daemon proxy."""
        try:
            if self.systemd_proxy_file.exists():
                self.systemd_proxy_file.unlink()
                typer.echo("Docker daemon proxy disabled")
            else:
                typer.echo(
                    "Docker daemon proxy config file not found, no need to disable",
                )
            return True
        except Exception as e:
            typer.echo(f"Failed to disable Docker daemon proxy: {e}", err=True)
            return False

    def check_proxy_status(self) -> None:
        """Check proxy status."""
        typer.echo("=== Docker Proxy Status ===")

        # Check client proxy
        if self.docker_config_file.exists():
            with open(self.docker_config_file) as f:
                config = json.load(f)
            if "proxies" in config:
                typer.echo("Docker client proxy: Enabled")
                proxy_info = config["proxies"]["default"]
                typer.echo(f"   HTTP Proxy: {proxy_info.get('httpProxy', 'N/A')}")
                typer.echo(f"   HTTPS Proxy: {proxy_info.get('httpsProxy', 'N/A')}")
                typer.echo(f"   No Proxy: {proxy_info.get('noProxy', 'N/A')}")
            else:
                typer.echo("Docker client proxy: Disabled")
        else:
            typer.echo("Docker client proxy: Disabled")

        # Check daemon proxy
        if self.systemd_proxy_file.exists():
            typer.echo("Docker daemon proxy: Enabled")
            with open(self.systemd_proxy_file) as f:
                content = f.read()
                typer.echo("   Configuration:")
                for line in content.strip().split("\n"):
                    if line.startswith("Environment="):
                        typer.echo(f"   {line}")
        else:
            typer.echo("Docker daemon proxy: Disabled")

    def enable_proxy(self, proxy_url: str | None = None) -> None:
        """Enable proxy."""
        if proxy_url:
            self.proxy_settings["http"] = proxy_url
            self.proxy_settings["https"] = proxy_url

        typer.echo("=== Enabling Docker Proxy ===")

        # Enable client proxy
        client_success = self.enable_docker_client_proxy()

        # Enable daemon proxy (requires root privileges)
        daemon_success = True
        if self.check_root():
            daemon_success = self.enable_docker_daemon_proxy()
            if daemon_success:
                self.restart_docker()
        else:
            typer.echo("Root privileges required for Docker daemon proxy")
            typer.echo("   Please run with sudo or configure daemon proxy manually")

        if client_success:
            typer.echo("Docker proxy enabled successfully!")
        else:
            typer.echo("Failed to enable Docker proxy", err=True)

    def disable_proxy(self) -> None:
        """Disable proxy."""
        typer.echo("=== Disabling Docker Proxy ===")

        # Disable client proxy
        client_success = self.disable_docker_client_proxy()

        # Disable daemon proxy (requires root privileges)
        daemon_success = True
        if self.check_root():
            daemon_success = self.disable_docker_daemon_proxy()
            if daemon_success:
                self.restart_docker()
        else:
            typer.echo("Root privileges required for Docker daemon proxy")
            typer.echo("   Please run with sudo or configure daemon proxy manually")

        if client_success:
            typer.echo("Docker proxy disabled successfully!")
        else:
            typer.echo("Failed to disable Docker proxy", err=True)


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
    r"""Check Docker proxy status.

    \b
    Examples:
        ./clash_docker status
    """
    DockerProxyManager().check_proxy_status()


@app.command()
def reset() -> None:
    r"""Reset all Docker proxy configurations.

    This will completely remove all Docker proxy settings including:
    - Docker client proxy configuration
    - Docker daemon proxy configuration

    \b
    Examples:
        ./clash_docker reset
    """
    manager = DockerProxyManager()
    typer.echo("=== Resetting Docker Proxy Configurations ===")
    typer.echo("This will remove:")
    typer.echo("- Docker client proxy configuration")
    typer.echo("- Docker daemon proxy configuration")

    manager.disable_proxy()
    typer.echo("All configurations have been reset")


if __name__ == "__main__":
    app()
